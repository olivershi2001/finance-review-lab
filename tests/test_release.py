"""Asset and release checks, not model performance measurements."""
import contextlib,importlib.util,io,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from frl.cli import export
import verify_suite

class AssetTests(unittest.TestCase):
    def test_independent_exported_workbook_checks(self):
        with contextlib.redirect_stdout(io.StringIO()):verify_suite.main()
    def test_every_export_is_blind_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            for folder in sorted((ROOT/'cases').iterdir()):
                output=Path(tmp)/(folder.name+'.zip');export(ROOT,folder.name,output)
                with zipfile.ZipFile(output) as z:
                    self.assertEqual(set(z.namelist()),{'model.xlsx','task.md','metadata.json'})
                    metadata=json.loads(z.read('metadata.json'))
                    self.assertEqual(set(metadata),{'case_id','version','split','units'})
                    self.assertNotIn('errors',metadata);self.assertNotIn('clean',metadata)
    def test_manifest_probe_base_matches_reference(self):
        for folder in sorted((ROOT/'references').iterdir()):
            manifest=json.loads((folder/'manifest.json').read_text());_,sheets,_=verify_suite.read(folder/'reference.xlsx')
            for error in manifest['errors']:
                for cell,value in error['probes'][0]['cells'].items():
                    verify_suite.close(verify_suite.n(sheets[error['sheet']],cell),verify_suite.D(str(value)))
    def test_empty_private_infrastructure_and_public_guard(self):
        script=ROOT/'scripts/init-private-workspace.py'
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'new-private'
            r=subprocess.run([sys.executable,str(script),str(out)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(list((out/'cases').iterdir()),[])
            state=json.loads((out/'isolation-checklist.json').read_text());self.assertEqual(state['status'],'not_validated')
        r=subprocess.run([sys.executable,str(script),str(ROOT/'forbidden-private')],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertFalse((ROOT/'forbidden-private').exists())
    def test_demo_is_only_simulated(self):
        data=json.loads((ROOT/'reports/demo-report.json').read_text())
        self.assertEqual(data['schema_version'],'1.0');self.assertTrue(data['runs'])
        self.assertEqual({r['mode'] for r in data['runs']},{'simulated'})
        self.assertIn('No model calls',data['notice'])
    def test_release_allowlist(self):
        spec=importlib.util.spec_from_file_location('package_release',ROOT/'scripts/make-release.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        files=list(module.selected());self.assertGreater(len(files),40)
        for _,rel in files:
            self.assertNotIn(rel.parts[0],{'runs','exports','node_modules','build-previews'})
            self.assertNotIn('__pycache__',rel.parts)
        self.assertIn('viewer/index.html',{str(rel) for _,rel in files})
if __name__=='__main__':unittest.main()
