"""Campaign planning fixtures, not model trials."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from frl.campaign import plan, load, status, init_next, validate_config

class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for i in range(4):
            case=f'dev-{i}'
            folder=self.root/'cases'/case;folder.mkdir(parents=True)
            (folder/'model.xlsx').write_bytes(b'workbook')
            (folder/'task.md').write_text('Audit')
            (folder/'metadata.json').write_text(json.dumps({'case_id':case,'version':'1','split':'public_dev','model_sha256':hashlib.sha256(b'workbook').hexdigest()}))
            ref=self.root/'references'/case;ref.mkdir(parents=True)
            (ref/'manifest.json').write_text(json.dumps({'case_id':case,'errors':[]}))
        prompts=self.root/'prompts';prompts.mkdir()
        for name in ('analyst.md','self-review.md','reviewer.md','revision.md'): (prompts/name).write_text(name)
        self.configs=[]
        for i in range(2):
            c={'model':f'Model {i}','product':'Codex','date':'2026-11-06','settings':{'reasoning':'high'},'tool_access':['formula inspection'],
               'attempt_cap':{'max_seconds':1200,'max_interactions':8},'infrastructure_retry_policy':{'max_retries':1,'only_confirmed_infrastructure':True}}
            path=self.root/f'config{i}.json';path.write_text(json.dumps(c));self.configs.append(path)
    def test_balanced_reproducible_frozen_24_trials(self):
        a=plan(self.root,'pilot',self.configs)
        self.assertEqual(len(a['queue']),24)
        self.assertEqual(len({t['run_id'] for t in a['queue']}),24)
        b=plan(self.root,'pilot2',self.configs)
        self.assertEqual([(q['case_id'],q['configuration_index'],q['repetition']) for q in a['queue']],[(q['case_id'],q['configuration_index'],q['repetition']) for q in b['queue']])
        for i in range(0,24,2): self.assertEqual({q['configuration_index'] for q in a['queue'][i:i+2]},{0,1})
        self.assertFalse((self.root/'runs').exists())
        self.assertEqual(status(self.root,'pilot')['initialized_trials'],0)
    def test_init_next_and_optional_stage_states(self):
        plan(self.root,'pilot',self.configs)
        first=init_next(self.root,'pilot')['run']['run_id']
        second=init_next(self.root,'pilot')['run']['run_id']
        self.assertNotEqual(first,second)
        result=status(self.root,'pilot');self.assertEqual(result['initialized_trials'],2)
        self.assertEqual(result['trials'][0]['stages']['review'],'not_planned')
        self.assertEqual(result['trials'][0]['stages']['analyst'],'pending')
    def test_branches_planned_explicitly(self):
        plan(self.root,'pilot',self.configs,branches=True)
        self.assertEqual(status(self.root,'pilot')['trials'][0]['stages']['review'],'pending')
    def test_plan_tamper_rejected(self):
        plan(self.root,'pilot',self.configs)
        path=self.root/'campaigns/pilot/plan.json';data=json.loads(path.read_text());data['seed']=1;path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):load(self.root,'pilot')
    def test_source_change_and_frozen_config_change_rejected(self):
        plan(self.root,'pilot',self.configs)
        (self.root/'campaigns/pilot/configuration-0.json').write_text('{}')
        with self.assertRaises(ValueError):load(self.root,'pilot')
    def test_reference_change_rejected(self):
        plan(self.root,'pilot',self.configs)
        (self.root/'references/dev-0/manifest.json').write_text('{}')
        with self.assertRaises(ValueError):init_next(self.root,'pilot')
    def test_blind_package_change_rejected(self):
        plan(self.root,'pilot',self.configs)
        (self.root/'campaigns/pilot/dev-0-blind.zip').write_bytes(b'broken')
        from zipfile import BadZipFile
        with self.assertRaises(BadZipFile):load(self.root,'pilot')
    def test_placeholder_caps_and_retry_rules_rejected(self):
        original=json.loads(self.configs[0].read_text())
        for patch in ({'model':'TODO'},{'attempt_cap':'20 min'},{'attempt_cap':{'max_seconds':0,'max_interactions':2}}, {'infrastructure_retry_policy':{'max_retries':8,'only_confirmed_infrastructure':True}}):
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError): validate_config({**original,**patch})
    def test_identical_configs_rejected(self):
        with self.assertRaises(ValueError):plan(self.root,'pilot',[self.configs[0],self.configs[0]])

if __name__=='__main__':unittest.main()
