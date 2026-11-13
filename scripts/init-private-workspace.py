"""Create empty external authoring folders; does not create unseen benchmark tasks."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);args=p.parse_args();dest=args.destination.resolve()
    if dest==ROOT or ROOT in dest.parents or dest in ROOT.parents:p.error('Choose a new directory outside the public release checkout')
    if dest.exists():p.error('Destination must not exist')
    dest.mkdir(parents=True)
    for folder in ['cases','references','runs']: (dest/folder).mkdir()
    (dest/'README.md').write_text('# Private authoring workspace\n\nEmpty infrastructure only. A separate directory does not provide model isolation. Do not claim these cases are unseen until evaluator permissions, context and network access have been independently controlled and tested. No private tasks have been created.\n')
    (dest/'isolation-checklist.json').write_text(json.dumps({'status':'not_validated','requirements':['Separate evaluator process/context','Allowlist blind input files only','Deny reference/source filesystem access','Prevent web lookup of public solutions','Document tool access and model settings','Test with unscored canary artifacts','Freeze dataset hashes before scored runs']},indent=2)+'\n')
    print('Created empty external authoring infrastructure:',dest)
if __name__=='__main__':main()
