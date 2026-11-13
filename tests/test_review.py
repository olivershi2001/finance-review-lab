"""Review workflow QA: all decisions here are simulated, never actual human review."""
import copy
import json
from pathlib import Path
import unittest
from frl.review import make_packet, render_packet, finalize_worksheet
from frl.grading import grade_submission


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((Path(__file__).resolve().parents[1]/'references/case-001/manifest.json').read_text())
        e=self.manifest['errors'][0]
        self.response={'findings':[{'sheet':e['sheet'],'cell':e['cell'],'diagnosis':e['diagnosis_required'],
            'corrected_formula':e['accepted_formula'],'correct_value':e['impact']['correct_value'],
            'original_minus_correct':e['impact']['original_minus_correct'],'downstream_cells':e['downstream_cells']}]}

    def test_uncompleted_packet_never_adjudicates(self):
        packet=make_packet(self.response,self.manifest,'opaque-001')
        self.assertIsNone(grade_submission(self.response,self.manifest,packet)['successful_audit'])
        with self.assertRaises(ValueError):finalize_worksheet(packet,self.response,self.manifest)

    def test_no_identity_fields_and_escaped_text(self):
        r=copy.deepcopy(self.response);r['findings'][0]['diagnosis']='<script>alert(1)</script>'
        packet=make_packet(r,self.manifest,'opaque-001')
        self.assertNotIn('configuration',packet);self.assertNotIn('model',packet)
        rendered=render_packet(r,self.manifest,packet)
        self.assertNotIn('<script>',rendered);self.assertIn('&lt;script&gt;',rendered)
        self.assertIn('detection:root-1',rendered)

    def test_simulated_completion_binds_exact_artifacts(self):
        packet=make_packet(self.response,self.manifest,'opaque-001')
        packet.update(reviewer_kind='human',reviewer='SIMULATED TEST ONLY')
        for item in packet['criteria'].values():item.update(verdict=True,evidence='SIMULATED TEST EVIDENCE ONLY')
        adjudication=finalize_worksheet(packet,self.response,self.manifest)
        self.assertTrue(grade_submission(self.response,self.manifest,adjudication)['successful_audit'])
        changed=copy.deepcopy(self.response);changed['findings'][0]['diagnosis']='changed'
        with self.assertRaises(ValueError):finalize_worksheet(packet,changed,self.manifest)
        changed=copy.deepcopy(self.manifest);changed['version']='new'
        with self.assertRaises(ValueError):finalize_worksheet(packet,self.response,changed)

    def test_cannot_drop_pending_or_use_empty_evidence(self):
        packet=make_packet(self.response,self.manifest,'opaque-001')
        packet.update(reviewer_kind='human',reviewer='SIMULATED TEST ONLY')
        with self.assertRaises(ValueError):finalize_worksheet(packet,self.response,self.manifest)
        packet['criteria'].pop('restraint')
        with self.assertRaises(ValueError):finalize_worksheet(packet,self.response,self.manifest)

    def test_clean_packet_still_requires_restraint(self):
        manifest={'case_id':'clean','errors':[]}
        self.assertEqual(set(make_packet({'findings':[]},manifest,'opaque')['criteria']),{'restraint'})

    def test_invalid_response_not_reviewable_as_success(self):
        with self.assertRaises(ValueError):make_packet({'findings':[],'status':'refused'},self.manifest,'opaque')


if __name__=='__main__':unittest.main()
