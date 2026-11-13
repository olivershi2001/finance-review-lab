"""Offline, immutable run capture. No subscription or provider automation."""
import argparse
import hashlib
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STAGES = ('analyst', 'self_review', 'review', 'revision')

def read(path):
    return json.loads(Path(path).read_text())

def digest(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')

def safe(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', value):
        raise ValueError('Invalid identifier')
    return value

def case_assets(root, case):
    folder = root / 'cases' / safe(case)
    metadata = read(folder / 'metadata.json')
    if metadata.get('case_id') != case:
        raise ValueError('Case metadata identifier mismatch')
    model_hash=metadata.get('model_sha256')
    if not isinstance(model_hash,str) or model_hash != digest((folder/'model.xlsx').read_bytes()):
        raise ValueError('Model bytes do not match case metadata hash')
    # Explicit allowlist: error counts, clean labels, reference hashes never escape.
    public = {k: metadata[k] for k in ('case_id', 'version', 'split', 'units') if k in metadata}
    public['case_id'] = case
    assets = {name: (folder / name).read_bytes() for name in ('model.xlsx', 'task.md')}
    assets['metadata.json'] = (json.dumps(public, sort_keys=True, indent=2)+'\n').encode()
    return assets

def dataset_hash(assets):
    return digest(b''.join(name.encode()+b'\0'+assets[name] for name in sorted(assets)))

def run_folder(root, run):
    return root / 'runs' / safe(run)

def verify_inputs(folder, record):
    if dataset_hash({p.name:p.read_bytes() for p in (folder/'inputs').iterdir()}) != record['dataset_hash']:
        raise ValueError('Frozen inputs changed')

def export(root, case, output):
    assets = case_assets(root, case)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in assets.items():
            archive.writestr(name, data)
    return {'output': str(output), 'dataset_hash': dataset_hash(assets)}

def init(root, args):
    config = read(args.config)
    required = ('model', 'product', 'date', 'settings', 'tool_access', 'attempt_cap', 'infrastructure_retry_policy')
    if any(k not in config for k in required):
        raise ValueError('Configuration requires: '+', '.join(required))
    if any(not isinstance(config[k], str) or not config[k].strip() for k in ('model','product','date')):
        raise ValueError('model/product/date must be nonempty strings')
    datetime.fromisoformat(config['date'].replace('Z','+00:00'))
    assets = case_assets(root, args.case)
    manifest_path = root/'references'/args.case/'manifest.json'
    manifest_hash = digest(manifest_path.read_bytes())
    if read(manifest_path).get('case_id') != args.case:
        raise ValueError('Reference manifest identifier mismatch')
    metadata = read(root/'cases'/args.case/'metadata.json')
    if args.mode == 'evaluation' and metadata.get('split') not in ('private', 'private_eval', 'released_eval'):
        raise ValueError('Headline evaluation requires a private or released_eval split')
    folder = run_folder(root, args.run)
    folder.mkdir(parents=True, exist_ok=False)
    record = {'run_id': args.run, 'case_id': args.case, 'mode': args.mode,
              'case_version': metadata.get('version'), 'split': metadata.get('split', 'development'),
              'category': metadata.get('category', 'unknown'), 'configuration': config,
              'dataset_hash': dataset_hash(assets), 'manifest_sha256':manifest_hash, 'created_at': datetime.now(timezone.utc).isoformat()}
    dump(folder/'run.json', record, True)
    # Freeze the exact blind bytes used, independent of later author edits.
    for name, data in assets.items():
        target = folder/'inputs'/name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
    return record

def capture(root, args):
    folder = run_folder(root, args.run)
    record = read(folder/'run.json')
    verify_inputs(folder, record)
    if args.elapsed_seconds is not None and (not math.isfinite(args.elapsed_seconds) or args.elapsed_seconds < 0):
        raise ValueError('Elapsed seconds must be finite and nonnegative')
    if args.interactions is not None and args.interactions < 0:
        raise ValueError('Interactions must be nonnegative')
    parents = {}
    if args.stage != 'analyst':
        initial = read(folder/'analyst'/'capture.json')
        if initial['status'] != 'completed':
            raise ValueError('Cannot branch an unsuccessful or infrastructure-failed capture')
        parents['analyst'] = initial['raw_sha256']
        if digest((folder/'analyst'/'raw.txt').read_bytes()) != initial['raw_sha256']:
            raise ValueError('Initial response integrity check failed')
    if args.stage == 'revision':
        review = read(folder/'review'/'capture.json')
        if digest((folder/'review'/'raw.txt').read_bytes()) != review['raw_sha256']:
            raise ValueError('Review integrity check failed')
        if review['status'] != 'completed':
            raise ValueError('Revision requires completed reviewer feedback')
        parents['review'] = review['raw_sha256']
    raw = Path(args.raw).read_bytes()
    response = read(args.response) if args.response else None
    if args.status == 'completed' and args.stage != 'review' and not isinstance(response, dict):
        raise ValueError('Completed audit stages require a structured JSON object')
    stage = folder/args.stage
    stage.mkdir(exist_ok=False)
    (stage/'raw.txt').write_bytes(raw)
    if response is not None:
        dump(stage/'response.json', response, True)
    capture_record = {'stage':args.stage, 'status':args.status, 'raw_sha256':digest(raw),
                      'parents':parents, 'captured_at':datetime.now(timezone.utc).isoformat(),
                      'operator_note':args.note, 'elapsed_seconds':args.elapsed_seconds, 'interactions':args.interactions}
    if response is not None:
        capture_record['response_sha256'] = digest((stage/'response.json').read_bytes())
    dump(stage/'capture.json', capture_record, True)
    return capture_record

def failure_metrics(manifest):
    count=len(manifest.get('errors',[]))
    return {
        'root_cause_recall':{'numerator':0,'denominator':count},
        'finding_precision':{'numerator':0,'denominator':0},
        'valid_repair_rate':{'numerator':0,'denominator':count},
        'numerical_impact_accuracy':{'numerator':0,'denominator':2*count},
        'propagation_accuracy':{'numerator':0,'denominator':count},
        'clean_case_pass':False if count==0 else None,
    }

def fill_failed_metrics(result, manifest):
    if result.get('successful_audit') is False and not result.get('metrics'):
        result['metrics']=failure_metrics(manifest)
    return result

def grade(root, args):
    from .grading import grade_submission
    folder = run_folder(root,args.run)
    record = read(folder/'run.json')
    verify_inputs(folder, record)
    stage = folder/args.stage
    if (stage/'grade.json').exists() and not args.adjudication:
        raise ValueError('Existing grade preserved; provide adjudication for a new revision')
    cap = read(stage/'capture.json')
    if args.stage == 'review':
        raise ValueError('Reviewer feedback is not a final audit')
    if digest((stage/'raw.txt').read_bytes()) != cap['raw_sha256']:
        raise ValueError('Raw response integrity check failed')
    if cap.get('response_sha256') and digest((stage/'response.json').read_bytes()) != cap['response_sha256']:
        raise ValueError('Parsed response integrity check failed')
    manifest_path = root/'references'/record['case_id']/'manifest.json'
    if digest(manifest_path.read_bytes()) != record['manifest_sha256']:
        raise ValueError('Reference manifest changed since run initialization')
    adjudication = read(args.adjudication) if args.adjudication else None
    if cap['status'] == 'infrastructure_failure':
        result = {'status':'infrastructure_failure', 'successful_audit':None}
    elif cap['status'] != 'completed':
        result = {'status':'adjudicated', 'successful_audit':False, 'deterministic_pass':False,
                  'metrics':{}, 'issues':['Attempt ended with '+cap['status']], 'capture_failure':cap['status']}
    else:
        response = read(stage/'response.json') if (stage/'response.json').exists() else None
        from .review import validate_adjudication
        adjudication = validate_adjudication(adjudication, response, read(manifest_path))
        result = grade_submission(response, read(manifest_path), adjudication=adjudication)
    if cap['status'] != 'infrastructure_failure':
        result=fill_failed_metrics(result,read(manifest_path))
    result = {'grade':result, 'manifest_sha256':digest(manifest_path.read_bytes()),
              'raw_sha256':cap['raw_sha256'], 'human_adjudication_supplied':adjudication is not None,
              'adjudication':adjudication}
    history = stage/'grade_history'
    history.mkdir(exist_ok=True)
    revision = len(list(history.glob('*.json'))) + 1
    result['revision'] = revision
    dump(history/f'{revision:04d}.json', result, True)
    dump(stage/'grade.json', result)
    return result

def report(root, output):
    runs = []
    for path in sorted((root/'runs').glob('*/run.json')):
        item = read(path)
        verify_inputs(path.parent,item)
        manifest_path=root/'references'/safe(item['case_id'])/'manifest.json'
        if digest(manifest_path.read_bytes()) != item['manifest_sha256']:
            raise ValueError('Reference manifest changed since run initialization')
        if item['mode']=='evaluation' and item['split'] not in ('private','private_eval','released_eval'):
            raise ValueError('Development cases cannot enter headline evaluation')
        item['stages'] = {}
        for name in STAGES:
            folder = path.parent/name
            if not (folder/'capture.json').exists():
                item['stages'][name] = {'status':'missing'}
                continue
            stage = read(folder/'capture.json')
            stage['raw'] = (folder/'raw.txt').read_text(errors='replace')
            stage['integrity_verified'] = digest((folder/'raw.txt').read_bytes()) == stage['raw_sha256']
            if (folder/'response.json').exists():
                stage['response'] = read(folder/'response.json')
                stage['integrity_verified'] &= digest((folder/'response.json').read_bytes()) == stage.get('response_sha256')
            if (folder/'grade.json').exists():
                stage['grading'] = read(folder/'grade.json')
                snapshot=stage['grading']
                historical=read(folder/'grade_history'/f"{snapshot['revision']:04d}.json")
                if snapshot != historical or snapshot['raw_sha256'] != stage['raw_sha256'] or snapshot['manifest_sha256'] != item['manifest_sha256']:
                    raise ValueError('Grade integrity check failed')
                if stage['status']=='completed':
                    from .grading import grade_submission
                    from .review import validate_adjudication
                    adjudication=validate_adjudication(snapshot.get('adjudication'),stage.get('response'),read(manifest_path))
                    computed=grade_submission(stage.get('response'),read(manifest_path),adjudication=adjudication)
                    computed=fill_failed_metrics(computed,read(manifest_path))
                    if computed != snapshot['grade']:
                        raise ValueError('Grade does not reproduce from captured response')
                elif stage['status']=='infrastructure_failure':
                    if snapshot['grade'].get('successful_audit') is not None:
                        raise ValueError('Infrastructure failure cannot be successful')
                else:
                    expected={'status':'adjudicated','successful_audit':False,'deterministic_pass':False,
                              'metrics':failure_metrics(read(manifest_path)),
                              'issues':['Attempt ended with '+stage['status']], 'capture_failure':stage['status']}
                    if snapshot['grade'] != expected:
                        raise ValueError('Failed capture grade does not reproduce')
            item['stages'][name] = stage
        runs.append(item)
    data = {'schema_version':'1.0', 'generated_at':datetime.now(timezone.utc).isoformat(),
            'notice':'Development and simulated runs are excluded from headline benchmark claims. Human review is required before verified publication.',
            'runs':runs}
    dump(Path(output), data)
    return {'output':str(output),'runs':len(runs)}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('export');p.add_argument('case');p.add_argument('output')
    p=commands.add_parser('init');p.add_argument('run');p.add_argument('case');p.add_argument('--config',required=True);p.add_argument('--mode',choices=('development','simulated','evaluation'),default='development')
    p=commands.add_parser('import');p.add_argument('run');p.add_argument('stage',choices=STAGES);p.add_argument('--raw',required=True);p.add_argument('--response');p.add_argument('--status',choices=('completed','malformed','refused','incomplete','infrastructure_failure'),default='completed');p.add_argument('--note',default='');p.add_argument('--elapsed-seconds',type=float);p.add_argument('--interactions',type=int)
    p=commands.add_parser('grade');p.add_argument('run');p.add_argument('stage',choices=STAGES);p.add_argument('--adjudication')
    p=commands.add_parser('report');p.add_argument('output')
    args=parser.parse_args(argv)
    try:
        if args.command=='export': result=export(args.root,args.case,args.output)
        elif args.command=='init': result=init(args.root,args)
        elif args.command=='import': result=capture(args.root,args)
        elif args.command=='grade': result=grade(args.root,args)
        else: result=report(args.root,args.output)
        print(json.dumps(result,indent=2))
        return 0
    except (ValueError,OSError,KeyError) as error:
        print(str(error),file=sys.stderr)
        return 2
