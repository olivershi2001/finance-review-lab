"""Generate SIMULATED fixture records through the real CLI. No models are called."""
import argparse, contextlib, copy, io, json, shutil, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from frl.cli import main

def dump(p,value):p.write_text(json.dumps(value,indent=2)+'\n');return p
def run(root,*args):
    with contextlib.redirect_stdout(io.StringIO()):
        result=main(['--root',str(root),*map(str,args)])
    if result not in (None,0):raise RuntimeError(f'CLI failed: {args}')
def correct(manifest):
    return {'findings':[{'sheet':e['sheet'],'cell':e['cell'],'diagnosis':e['diagnosis_required'],
                         'existing_formula':e['existing_formula'],'corrected_formula':e['accepted_formula'],
                         'correct_value':e['impact']['correct_value'],'original_minus_correct':e['impact']['original_minus_correct'],
                         'downstream_cells':e['downstream_cells'],'explanation':'SIMULATED fixture using the public reference answer, not a model response.'} for e in manifest['errors']]}
def main_demo():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'reports/demo-report.json');args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='frl-fixtures-') as tmp:
        temp=Path(tmp)
        shutil.copytree(ROOT/'cases',temp/'cases');shutil.copytree(ROOT/'references',temp/'references')
        config=dump(temp/'configuration.json',{'model':'SIMULATED fixture; no model','product':'software test',
          'date':'2026-11-05','settings':{'fixture':True},'tool_access':['none'],
          'attempt_cap':'Not applicable: constructed software fixtures','infrastructure_retry_policy':'Not applicable'})
        def capture(rid,stage,response,status='completed'):
            raw=temp/f'{rid}-{stage}.txt';raw.write_text('SIMULATED SUBMISSION — no model was evaluated.\n'+json.dumps(response))
            structured=dump(temp/f'{rid}-{stage}.json',response)
            run(temp,'import',rid,stage,'--raw',raw,'--response',structured,'--status',status,'--note','Constructed fixture, not measured work')
        def grade(rid,stage,manifest,human=False):
            extra=[]
            if human:
                criteria={'restraint':{'verdict':True,'evidence':'SIMULATED adjudication fixture; not a real human review.'}}
                for e in manifest['errors']:
                    for k in ['detection','explanation']:criteria[k+':'+e['id']]={'verdict':True,'evidence':'SIMULATED adjudication fixture asserting the reference diagnosis.'}
                ap=dump(temp/f'{rid}-{stage}-adjudication.json',{'criteria':criteria});extra=['--adjudication',ap]
            run(temp,'grade',rid,stage,*extra)
        for i,cid in enumerate(['case-001','dev-002','dev-003','dev-004']):
            manifest=json.loads((temp/'references'/cid/'manifest.json').read_text());rid=f'simulated-{i+1:02d}'
            run(temp,'init',rid,cid,'--config',config,'--mode','simulated')
            answer=correct(manifest)
            if i==0:
                capture(rid,'analyst',{'findings':[]});grade(rid,'analyst',manifest,True)
                capture(rid,'self_review',answer);grade(rid,'self_review',manifest,True)
            elif i==1:
                capture(rid,'analyst',answer);grade(rid,'analyst',manifest,True)
                capture(rid,'review',{'feedback':'SIMULATED bad advice: use opening rather than average debt.'})
                wrong=copy.deepcopy(answer);wrong['findings'][0]['corrected_formula']='=G9*G19'
                capture(rid,'revision',wrong);grade(rid,'revision',manifest,True)
            elif i==2:
                capture(rid,'analyst',{'text':'SIMULATED malformed audit response'},'malformed');grade(rid,'analyst',manifest)
            else:
                capture(rid,'analyst',answer);grade(rid,'analyst',manifest,True)
        run(temp,'report',args.output)
    report=json.loads(args.output.read_text());report['notice']='SIMULATED FIXTURES ONLY. No model calls or real human adjudications. Demonstrates successful, failed, helpful and harmful transitions.'
    dump(args.output,report)
    print('Created explicitly simulated viewer report:',args.output)
if __name__=='__main__':main_demo()
