"""Blinded metadata review packets; this module never supplies human decisions."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from .grading import grade_submission


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def make_packet(response, manifest, review_id):
    """Inputs intentionally omit run/model metadata. Answer self-identification remains visible."""
    if not isinstance(review_id, str) or not review_id.strip():
        raise ValueError('An opaque review identifier is required')
    grade = grade_submission(response, manifest)
    if grade['status'] == 'invalid':
        raise ValueError('Invalid/refused submissions are failures, not successful-audit human review packets')
    criteria = {}
    for key in grade['pending_adjudication']:
        criteria[key] = {'verdict': None, 'evidence': ''}
    return {'schema_version': '1', 'review_id': review_id,
            'response_sha256': fingerprint(response), 'manifest_sha256': fingerprint(manifest),
            'reviewer_kind': None, 'reviewer': '', 'criteria': criteria}


def render_packet(response, manifest, worksheet):
    """HTML includes escaped source, reference expectations and pending prompts, no model metadata."""
    esc = lambda value: html.escape(str(value), quote=True)
    rows=[]
    for key in worksheet['criteria']:
        kind, _, eid = key.partition(':')
        error = next((e for e in manifest['errors'] if e['id'] == eid), None)
        expectation = 'Review every proposed change; determine whether any material false correction is present.'
        if error:
            expectation = error.get('diagnosis_required', '')
            if kind == 'repair':
                expectation += '\nValidate the unsupported formula in Excel or record an explicit financial equivalence analysis. Canonical example: '+str(error.get('accepted_formula', error.get('accepted_formulas', [])))
        rows.append('<section><h2>'+esc(key)+'</h2><pre>'+esc(expectation)+'</pre><p>Enter your decision and exact evidence in worksheet.json. Null means not reviewed.</p></section>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Finance audit human review</title>
<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f7;padding:16px}section{border-top:1px solid #ccc;margin-top:24px}</style>
<h1>Human review: '''+esc(worksheet['review_id'])+'''</h1><p>No model/configuration metadata is supplied. The answer itself may identify its author; this is metadata blinding, not guaranteed anonymity. Reference answers are visible to this grader. This packet contains no completed human decisions.</p>
<h2>Original structured response (exact JSON values)</h2><pre>'''+esc(json.dumps(response, indent=2, ensure_ascii=False))+'''</pre>
<h2>Deterministic grading evidence</h2><pre>'''+esc(json.dumps(grade_submission(response,manifest),indent=2))+'''</pre>
'''+''.join(rows)+'''<p>Evidence must quote the relevant submitted answer or explicitly identify an omission, and explain the decision. Do not paste the reference answer as if it were submission evidence.</p></html>'''


def finalize_worksheet(worksheet, response, manifest):
    if not isinstance(worksheet, dict) or worksheet.get('schema_version') != '1':
        raise ValueError('Unsupported human review worksheet schema')
    expected=make_packet(response,manifest,worksheet.get('review_id'))
    for key in ('response_sha256','manifest_sha256'):
        if worksheet.get(key) != expected[key]:
            raise ValueError('Review packet binding mismatch: '+key)
    if worksheet.get('reviewer_kind') != 'human' or not isinstance(worksheet.get('reviewer'),str) or not worksheet['reviewer'].strip():
        raise ValueError('A human reviewer must identify and attest to their review')
    criteria=worksheet.get('criteria')
    if not isinstance(criteria,dict) or set(criteria) != set(expected['criteria']):
        raise ValueError('Worksheet criteria differ from required pending criteria')
    for key, item in criteria.items():
        if not isinstance(item,dict) or type(item.get('verdict')) is not bool or not isinstance(item.get('evidence'),str) or not item['evidence'].strip():
            raise ValueError('Incomplete evidence-bearing decision: '+key)
    return {**worksheet, 'criteria':criteria}


def validate_adjudication(adjudication, response, manifest):
    """Validate bound worksheets; preserve legacy direct criterion maps."""
    if isinstance(adjudication, dict) and any(key in adjudication for key in
            ('schema_version', 'review_id', 'response_sha256', 'manifest_sha256', 'reviewer_kind')):
        return finalize_worksheet(adjudication, response, manifest)
    return adjudication


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','finalize'])
    parser.add_argument('--response',required=True);parser.add_argument('--manifest',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--review-id');parser.add_argument('--worksheet')
    args=parser.parse_args()
    read=lambda p:json.loads(Path(p).read_text())
    response,manifest=read(args.response),read(args.manifest)
    output=Path(args.output)
    if args.action=='prepare':
        packet=make_packet(response,manifest,args.review_id)
        if output.exists(): raise ValueError('Output directory already exists; preserve original review')
        output.mkdir(parents=True)
        (output/'worksheet.json').write_text(json.dumps(packet,indent=2)+'\n')
        (output/'review.html').write_text(render_packet(response,manifest,packet))
    else:
        if not args.worksheet: parser.error('--worksheet is required for finalize')
        packet=finalize_worksheet(read(args.worksheet),response,manifest)
        if output.exists(): raise ValueError('Output already exists; preserve original adjudication')
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(packet,indent=2)+'\n')


if __name__=='__main__':main()
