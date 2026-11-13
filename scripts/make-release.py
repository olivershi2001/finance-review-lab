"""Create an allowlisted source archive, excluding local runs and dependencies."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
TOP_FILES={'README.md','CONTRIBUTING.md','LICENSE','LICENSE-DATA','.gitignore','case-plan.csv','verify_case.py','verify_suite.py'}
DIRECTORIES={'cases','references','frl','scripts','tests','viewer','docs','prompts','templates','.github'}
def selected():
    for p in sorted(ROOT.rglob('*')):
        relative=p.relative_to(ROOT)
        if any(x in ('node_modules','__pycache__','.git') for x in relative.parts):continue
        if not p.is_file() or p.is_symlink() or p.name.endswith('.inspect.ndjson'):continue
        if relative.as_posix() in TOP_FILES or relative.parts[0] in DIRECTORIES or relative.as_posix() in {'reports/demo-report.json','reports/native-excel-validation.json'}:yield p,relative
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);args=p.parse_args()
    files=list(selected());assert files
    for file,rel in files:
        assert not any(x.startswith('.env') for x in rel.parts)
        if file.suffix in {'.py','.mjs','.js','.md','.json','.cjs','.html','.css','.yml'}:
            text=file.read_text();assert ('/'+'Users'+'/') not in text and ('/'+'private'+'/var/') not in text,f'Personal path in {rel}'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    manifest={str(rel):hashlib.sha256(file.read_bytes()).hexdigest() for file,rel in files}
    with zipfile.ZipFile(args.output,'x',zipfile.ZIP_DEFLATED) as z:
        for file,rel in files:z.write(file,'finance-eval-lab/'+str(rel))
        z.writestr('finance-eval-lab/RELEASE-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    print(f'Packaged {len(files)} allowlisted files into {args.output}')
if __name__=='__main__':main()
