"""Native evidence integrity and shared-formula comparison; no Excel automation."""
import importlib.util
import json
from pathlib import Path
import unittest
from verify_suite import sha

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_verifier', ROOT/'scripts/verify-native-excel.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeEvidenceTests(unittest.TestCase):
    def test_shared_formula_relative_and_absolute_refs(self):
        self.assertEqual(native.translate_shared('SUM($E20:F20)+G$4+$A$1', 'F24', 'H25'),
                         'SUM($E21:H21)+I$4+$A$1')
        self.assertEqual(native.translate_shared('IF(F20=0,"A1",\'A1\'!F20)', 'F24', 'G24'),
                         'IF(G20=0,"A1",\'A1\'!G20)')

    def test_saved_evidence_matches_current_deliverables(self):
        report=json.loads((ROOT/'reports/native-excel-validation.json').read_text())
        self.assertEqual(report['status'],'passed')
        self.assertEqual(report['workbooks_compared'],8)
        self.assertEqual(len(report['results']),8)
        self.assertEqual({(x['case_id'],x['version']) for x in report['results']},
                         {(cid,kind) for cid in ('case-001','dev-002','dev-003','dev-004') for kind in ('cases','references')})
        for item in report['results']:
            name='model.xlsx' if item['version']=='cases' else 'reference.xlsx'
            self.assertEqual(item['source_sha256'],sha(ROOT/item['version']/item['case_id']/name))
            self.assertGreater(item['formula_caches_compared'],0)
        self.assertEqual(report['formula_caches_compared'],sum(x['formula_caches_compared'] for x in report['results']))


if __name__=='__main__':unittest.main()
