import contextlib
import io
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from frl.cli import main

class RunWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        folder=self.root/'cases'/'case-001';folder.mkdir(parents=True)
        (folder/'model.xlsx').write_bytes(b'workbook')
        (folder/'task.md').write_text('Audit this model')
        (folder/'metadata.json').write_text(json.dumps({'case_id':'case-001','version':'1','split':'development','category':'cash_flow','model_sha256':hashlib.sha256(b'workbook').hexdigest(),'is_clean':False,'errors':['secret']}))
        (folder/'answer-key.md').write_text('secret')
        ref=self.root/'references'/'case-001';ref.mkdir(parents=True);(ref/'manifest.json').write_text('{"case_id":"case-001","errors":[]}')
        self.config=self.root/'config.json';self.config.write_text(json.dumps({'model':'unknown','product':'manual','date':'2026-11-05','settings':{},'tool_access':['workbook'],'attempt_cap':'20 min','infrastructure_retry_policy':'one confirmed failure'}))
        self.raw=self.root/'raw.txt';self.raw.write_text('Original answer\n')
        self.response=self.root/'response.json';self.response.write_text('{"findings":[]}')
    def cli(self,*args):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return main(['--root',str(self.root),*map(str,args)])
    def init(self):
        self.assertEqual(self.cli('init','r1','case-001','--config',self.config),0)
    def capture(self,stage):
        return self.cli('import','r1',stage,'--raw',self.raw,'--response',self.response)
    def test_export_allowlist_and_no_overwrite(self):
        output=self.root/'blind.zip'
        self.assertEqual(self.cli('export','case-001',output),0)
        with zipfile.ZipFile(output) as z:
            self.assertEqual(set(z.namelist()),{'model.xlsx','task.md','metadata.json'})
            self.assertNotIn('errors',json.loads(z.read('metadata.json')))
        self.assertEqual(self.cli('export','case-001',output),2)
    def test_branch_parent_enforcement_immutability_and_hashes(self):
        self.init()
        self.assertEqual(self.capture('self_review'),2)
        self.assertEqual(self.capture('analyst'),0)
        self.assertEqual(self.capture('analyst'),2)
        self.assertEqual(self.capture('revision'),2)
        self.assertEqual(self.capture('review'),0)
        self.assertEqual(self.capture('revision'),0)
        analyst=json.loads((self.root/'runs/r1/analyst/capture.json').read_text())
        revision=json.loads((self.root/'runs/r1/revision/capture.json').read_text())
        self.assertEqual(revision['parents']['analyst'],analyst['raw_sha256'])
        (self.root/'runs/r1/analyst/raw.txt').write_text('tampered')
        self.assertEqual(self.capture('self_review'),2)
    def test_input_tamper_rejected(self):
        self.init();(self.root/'runs/r1/inputs/task.md').write_text('changed')
        self.assertEqual(self.capture('analyst'),2)
    def test_report_preserves_missing_and_infra(self):
        self.init()
        self.assertEqual(self.cli('import','r1','analyst','--raw',self.raw,'--status','infrastructure_failure'),0)
        output=self.root/'report.json';self.assertEqual(self.cli('report',output),0)
        item=json.loads(output.read_text())['runs'][0]
        self.assertEqual(item['mode'],'development')
        self.assertEqual(item['stages']['analyst']['status'],'infrastructure_failure')
        self.assertEqual(item['stages']['revision']['status'],'missing')
    def test_failed_initial_cannot_spawn_review(self):
        self.init()
        self.assertEqual(self.cli('import','r1','analyst','--raw',self.raw,'--status','refused'),0)
        self.assertEqual(self.capture('review'),2)
    def test_grade_integrates_and_stays_provisional(self):
        self.init();self.assertEqual(self.capture('analyst'),0)
        self.assertEqual(self.cli('grade','r1','analyst'),0)
        grade=json.loads((self.root/'runs/r1/analyst/grade.json').read_text())
        self.assertEqual(grade['grade']['status'],'provisional')
        self.assertIsNone(grade['grade']['successful_audit'])
        self.assertEqual(self.cli('grade','r1','analyst'),2)
        adjud=self.root/'human.json';adjud.write_text('{"restraint":{"verdict":true,"evidence":"Inspected no-findings response"}}')
        self.assertEqual(self.cli('grade','r1','analyst','--adjudication',adjud),0)
        self.assertEqual(len(list((self.root/'runs/r1/analyst/grade_history').glob('*.json'))),2)
        self.assertTrue(json.loads((self.root/'runs/r1/analyst/grade.json').read_text())['grade']['successful_audit'])
    def test_changed_reference_cannot_be_graded(self):
        self.init();self.assertEqual(self.capture('analyst'),0)
        (self.root/'references/case-001/manifest.json').write_text('{"errors":[],"changed":true}')
        self.assertEqual(self.cli('grade','r1','analyst'),2)

    def test_review_packet_binding_enforced_by_cli_and_report(self):
        from frl.review import make_packet
        self.init();self.assertEqual(self.capture('analyst'),0)
        response=json.loads(self.response.read_text())
        manifest=json.loads((self.root/'references/case-001/manifest.json').read_text())
        packet=make_packet(response,manifest,'opaque-test')
        packet.update(reviewer_kind='human',reviewer='SIMULATED TEST ONLY')
        for item in packet['criteria'].values():
            item.update(verdict=True,evidence='SIMULATED TEST EVIDENCE ONLY')
        adjud=self.root/'review.json'
        packet['response_sha256']='wrong';adjud.write_text(json.dumps(packet))
        self.assertEqual(self.cli('grade','r1','analyst','--adjudication',adjud),2)
        self.assertFalse((self.root/'runs/r1/analyst/grade.json').exists())
        packet=make_packet(response,manifest,'opaque-test')
        packet.update(reviewer_kind='human',reviewer='SIMULATED TEST ONLY')
        for item in packet['criteria'].values():
            item.update(verdict=True,evidence='SIMULATED TEST EVIDENCE ONLY')
        adjud.write_text(json.dumps(packet))
        self.assertEqual(self.cli('grade','r1','analyst','--adjudication',adjud),0)
        self.assertEqual(self.cli('report',self.root/'report.json'),0)
        gradepath=self.root/'runs/r1/analyst/grade.json'
        grade=json.loads(gradepath.read_text());grade['adjudication']['manifest_sha256']='wrong'
        gradepath.write_text(json.dumps(grade))
        (gradepath.parent/'grade_history/0001.json').write_text(json.dumps(grade))
        self.assertEqual(self.cli('report',self.root/'tampered-report.json'),2)
    def test_failed_status_with_valid_answer_cannot_pass(self):
        for status in ('refused','malformed','incomplete'):
            with self.subTest(status=status):
                run='failure-'+status
                self.assertEqual(self.cli('init',run,'case-001','--config',self.config),0)
                self.assertEqual(self.cli('import',run,'analyst','--raw',self.raw,'--response',self.response,'--status',status),0)
                self.assertEqual(self.cli('grade',run,'analyst'),0)
                grade=json.loads((self.root/'runs'/run/'analyst/grade.json').read_text())
                self.assertIs(grade['grade']['successful_audit'],False)
    def test_failed_status_counts_reference_denominators(self):
        ref=self.root/'references/case-001/manifest.json'
        ref.write_text('{"case_id":"case-001","errors":[{"id":"one"},{"id":"two"}]}')
        self.init()
        self.assertEqual(self.cli('import','r1','analyst','--raw',self.raw,'--status','refused'),0)
        self.assertEqual(self.cli('grade','r1','analyst'),0)
        g=json.loads((self.root/'runs/r1/analyst/grade.json').read_text())['grade']
        self.assertEqual(g['metrics']['root_cause_recall'],{'numerator':0,'denominator':2})
        self.assertEqual(g['metrics']['numerical_impact_accuracy'],{'numerator':0,'denominator':4})
    def test_case_metadata_mismatch_blocks_export_and_init(self):
        metadata=self.root/'cases/case-001/metadata.json'
        m=json.loads(metadata.read_text());m['case_id']='other';metadata.write_text(json.dumps(m))
        self.assertEqual(self.cli('export','case-001',self.root/'bad.zip'),2)
        self.assertEqual(self.cli('init','r1','case-001','--config',self.config),2)
    def test_case_model_hash_mismatch_blocks_export_and_init(self):
        (self.root/'cases/case-001/model.xlsx').write_bytes(b'edited')
        self.assertEqual(self.cli('export','case-001',self.root/'bad.zip'),2)
        self.assertEqual(self.cli('init','r1','case-001','--config',self.config),2)
    def test_public_case_cannot_claim_evaluation_mode(self):
        self.assertEqual(self.cli('init','fake-score','case-001','--config',self.config,'--mode','evaluation'),2)
    def test_effort_capture_and_validation(self):
        self.init()
        self.assertEqual(self.cli('import','r1','analyst','--raw',self.raw,'--response',self.response,'--elapsed-seconds','nan'),2)
        self.assertEqual(self.cli('import','r1','analyst','--raw',self.raw,'--response',self.response,'--interactions','-1'),2)
        self.assertEqual(self.cli('import','r1','analyst','--raw',self.raw,'--response',self.response,'--elapsed-seconds','12.5','--interactions','2'),0)
        cap=json.loads((self.root/'runs/r1/analyst/capture.json').read_text())
        self.assertEqual(cap['elapsed_seconds'],12.5);self.assertEqual(cap['interactions'],2)
    def test_grade_and_report_reject_changed_frozen_inputs(self):
        self.init();self.capture('analyst')
        (self.root/'runs/r1/inputs/model.xlsx').write_bytes(b'changed')
        self.assertEqual(self.cli('grade','r1','analyst'),2)
        self.assertEqual(self.cli('report',self.root/'report.json'),2)
    def test_report_rejects_tampered_grade(self):
        self.init();self.capture('analyst');self.cli('grade','r1','analyst')
        path=self.root/'runs/r1/analyst/grade.json';g=json.loads(path.read_text())
        g['grade']['successful_audit']=True;path.write_text(json.dumps(g))
        self.assertEqual(self.cli('report',self.root/'report.json'),2)
    def test_report_recomputes_even_if_history_also_tampered(self):
        self.init();self.capture('analyst');self.cli('grade','r1','analyst')
        path=self.root/'runs/r1/analyst/grade.json';g=json.loads(path.read_text())
        g['grade']['successful_audit']=True
        for target in (path,path.parent/'grade_history/0001.json'):
            target.write_text(json.dumps(g))
        self.assertEqual(self.cli('report',self.root/'report.json'),2)
    def test_empty_report_is_not_a_leaderboard(self):
        output=self.root/'report.json';self.assertEqual(self.cli('report',output),0)
        self.assertEqual(json.loads(output.read_text())['runs'],[])
    def test_identifiers_cannot_escape_runs(self):
        self.assertEqual(self.cli('init','../escape','case-001','--config',self.config),2)
    def test_missing_config_fields_rejected(self):
        self.config.write_text('{"model":"x"}')
        self.assertEqual(self.cli('init','r1','case-001','--config',self.config),2)

if __name__=='__main__':unittest.main()
