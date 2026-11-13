"""Frozen manual pilot queues. Does not execute models or subscriptions."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace
import zipfile
from . import cli


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def validate_config(config):
    for field in ('model', 'product', 'date'):
        value=config.get(field)
        if not isinstance(value,str) or not value.strip() or value.strip().lower() in ('unknown','n/a','none') or any(x in value.lower() for x in ('placeholder','replace','todo','tbd','your model','example')):
            raise ValueError('Set a real '+field)
    datetime.fromisoformat(config['date'].replace('Z','+00:00'))
    if not isinstance(config.get('settings'),dict) or not isinstance(config.get('tool_access'),list) or not config['tool_access']:
        raise ValueError('Record settings object and nonempty tool_access list')
    cap=config.get('attempt_cap')
    if not isinstance(cap,dict):
        raise ValueError('attempt_cap requires positive max_seconds and max_interactions')
    for key in ('max_seconds','max_interactions'):
        if type(cap.get(key)) is not int or cap[key]<=0:
            raise ValueError('attempt_cap requires positive integer '+key)
    retry=config.get('infrastructure_retry_policy')
    if not isinstance(retry,dict) or type(retry.get('max_retries')) is not int or not 0<=retry['max_retries']<=3 or retry.get('only_confirmed_infrastructure') is not True:
        raise ValueError('Retry policy requires max_retries 0..3 and only_confirmed_infrastructure true')


def plan(root, campaign, configurations, repetitions=3, seed=1729, branches=False):
    cli.safe(campaign)
    if len(configurations)!=2 or type(repetitions) is not int or repetitions<1:
        raise ValueError('Pilot requires two configurations and positive repetitions')
    configs=[cli.read(p) for p in configurations]
    for config in configs: validate_config(config)
    hashes=[cli.digest(canonical(c)) for c in configs]
    if hashes[0]==hashes[1]: raise ValueError('Configurations must differ')
    cases=[]; payloads={}
    for folder in sorted((root/'cases').iterdir()):
        if not folder.is_dir() or not (folder/'metadata.json').exists(): continue
        meta=cli.read(folder/'metadata.json')
        if meta.get('split') not in ('public_dev','development'): continue
        assets=cli.case_assets(root,folder.name)
        manifest=root/'references'/folder.name/'manifest.json'
        cases.append({'case_id':folder.name,'case_version':meta.get('version'),'dataset_hash':cli.dataset_hash(assets),'manifest_sha256':cli.digest(manifest.read_bytes())})
        payloads[folder.name]=assets
    if len(cases)!=4: raise ValueError('Pilot requires exactly four public development cases')
    prompts={name:(root/'prompts'/name).read_bytes() for name in ('analyst.md','self-review.md','reviewer.md','revision.md')}
    rng=random.Random(seed)
    blocks=[(case,rep) for case in cases for rep in range(1,repetitions+1)]
    rng.shuffle(blocks)
    queue=[]
    for case,rep in blocks:
        order=[0,1];rng.shuffle(order)
        for index in order:
            queue.append({'run_id':f'{campaign}-c{index+1}-{case["case_id"]}-r{rep}', 'case_id':case['case_id'],'configuration_index':index,'repetition':rep,
                          'planned_stages':['analyst','self_review','review','revision'] if branches else ['analyst']})
    content={'schema_version':'1.0','campaign_id':campaign,'mode':'development','seed':seed,'repetitions':repetitions,
             'configurations':configs,'configuration_hashes':hashes,'cases':cases,'queue':queue,
             'prompt_hashes':{name:cli.digest(data) for name,data in prompts.items()},
             'notice':'Planned manual development trials; no measured results. References stay with operator, never evaluator.'}
    content['plan_sha256']=cli.digest(canonical(content))
    folder=root/'campaigns'/campaign
    folder.mkdir(parents=True,exist_ok=False)
    cli.dump(folder/'plan.json',content,True)
    for index,config in enumerate(configs): cli.dump(folder/f'configuration-{index}.json',config,True)
    for case,assets in payloads.items():
        with zipfile.ZipFile(folder/f'{case}-blind.zip','x',zipfile.ZIP_DEFLATED) as archive:
            for name,data in assets.items(): archive.writestr(name,data)
            # Identical analyst instructions across cases/configurations.
            archive.writestr('analyst-prompt.md',prompts['analyst.md'])
    (folder/'prompts').mkdir()
    for name,data in prompts.items(): (folder/'prompts'/name).write_bytes(data)
    return content


def load(root,campaign):
    folder=root/'campaigns'/cli.safe(campaign)
    content=cli.read(folder/'plan.json');expected=content.pop('plan_sha256')
    if cli.digest(canonical(content))!=expected: raise ValueError('Campaign plan changed')
    content['plan_sha256']=expected
    for index,expected_config in enumerate(content['configuration_hashes']):
        if cli.digest(canonical(cli.read(folder/f'configuration-{index}.json')))!=expected_config:
            raise ValueError('Frozen configuration changed')
    for name,expected_prompt in content['prompt_hashes'].items():
        if cli.digest((folder/'prompts'/name).read_bytes())!=expected_prompt: raise ValueError('Frozen prompt changed')
    for case in content['cases']:
        assets=cli.case_assets(root,case['case_id'])
        if cli.dataset_hash(assets)!=case['dataset_hash'] or cli.digest((root/'references'/case['case_id']/'manifest.json').read_bytes())!=case['manifest_sha256']:
            raise ValueError('Case or reference changed since campaign freeze')
        with zipfile.ZipFile(folder/f'{case["case_id"]}-blind.zip') as archive:
            expected_members=set(assets)|{'analyst-prompt.md'}
            if set(archive.namelist())!=expected_members: raise ValueError('Blind package members changed')
            for name,data in assets.items():
                if archive.read(name)!=data: raise ValueError('Blind package changed')
            if cli.digest(archive.read('analyst-prompt.md'))!=content['prompt_hashes']['analyst.md']:
                raise ValueError('Packaged prompt changed')
    return folder,content


def status(root,campaign):
    _,content=load(root,campaign)
    trials=[]
    for item in content['queue']:
        folder=root/'runs'/item['run_id']
        run_status='planned'
        stages={}
        if folder.exists() and not (folder/'run.json').exists():
            raise ValueError('Incomplete run initialization requires operator inspection: '+item['run_id'])
        if (folder/'run.json').exists():
            record=cli.read(folder/'run.json');cli.verify_inputs(folder,record)
            if record['dataset_hash']!=next(c['dataset_hash'] for c in content['cases'] if c['case_id']==item['case_id']) or cli.digest(canonical(record['configuration']))!=content['configuration_hashes'][item['configuration_index']]:
                raise ValueError('Run does not match frozen campaign')
            run_status='initialized'
        for stage in cli.STAGES:
            path=folder/stage/'capture.json'
            if path.exists():
                cap=cli.read(path)
                if cli.digest((path.parent/'raw.txt').read_bytes())!=cap['raw_sha256']: raise ValueError('Captured response changed')
                stages[stage]=cap['status']
                if stage=='analyst': run_status=cap['status']
            else: stages[stage]='pending' if stage in item['planned_stages'] else 'not_planned'
        trials.append({**item,'status':run_status,'stages':stages})
    return {'campaign_id':campaign,'plan_sha256':content['plan_sha256'],'planned_trials':len(trials),
            'initialized_trials':sum(t['status']!='planned' for t in trials),'trials':trials,
            'retry_policy_note':'Confirmed infrastructure failures remain recorded. Retry scheduling is manual and must follow frozen configuration policy; no silent retry or replacement.'}


def init_next(root,campaign):
    folder,content=load(root,campaign)
    for trial in content['queue']:
        if (root/'runs'/trial['run_id']).exists():
            if not (root/'runs'/trial['run_id']/'run.json').exists():
                raise ValueError('Incomplete run initialization requires operator inspection: '+trial['run_id'])
            continue
        record=cli.init(root,SimpleNamespace(config=folder/f'configuration-{trial["configuration_index"]}.json',case=trial['case_id'],run=trial['run_id'],mode='development'))
        return {'run':record,'blind_package':str(folder/f'{trial["case_id"]}-blind.zip'),'planned_stages':trial['planned_stages'],'notice':'Initialized only. Transfer package to isolated fresh session; no model executed.'}
    return {'notice':'All planned trials initialized. No additional runs created.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('plan');p.add_argument('campaign');p.add_argument('--config',action='append',required=True);p.add_argument('--repetitions',type=int,default=3);p.add_argument('--seed',type=int,default=1729);p.add_argument('--branches',action='store_true')
    for command in ('status','init-next'): p=sub.add_parser(command);p.add_argument('campaign')
    args=parser.parse_args(argv)
    try:
        if args.command=='plan': result=plan(args.root,args.campaign,args.config,args.repetitions,args.seed,args.branches)
        elif args.command=='status': result=status(args.root,args.campaign)
        else: result=init_next(args.root,args.campaign)
        print(json.dumps(result,indent=2));return 0
    except (ValueError,OSError,KeyError,zipfile.BadZipFile) as error:
        print(str(error),file=sys.stderr);return 2

if __name__=='__main__': raise SystemExit(main())
