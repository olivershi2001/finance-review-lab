"""Controlled simulated submissions, never measured model results."""
import copy
import json
from pathlib import Path
import unittest
from frl.grading import evaluate_formula, NeedsReview, grade_submission, validate_submission


def manifest():
    return {'case_id':'demo','errors':[{'id':'sign','sheet':'Cash Flow','cell':'I40',
        'accepted_formulas':['=I35-I38'],
        'probes':[{'cells':{'I35':100,'I38':20},'expected':80},
                  {'cells':{'I35':120,'I38':-5},'expected':125},
                  {'cells':{'I35':60,'I38':0},'expected':60}],
        'impact':{'correct_value':80,'original_minus_correct':40,'tolerance':0.001},
        'downstream_cells':['I45']}]}


def response(formula='=I35-I38'):
    return {'findings':[{'sheet':'Cash Flow','cell':'I40','diagnosis':'Working capital sign',
        'corrected_formula':formula,'correct_value':80,'original_minus_correct':40,'downstream_cells':['I45']}]}


def human():
    return {key:{'verdict':True,'evidence':'Operator checked the original submitted text.'}
            for key in ('detection:sign','explanation:sign','restraint')}


class GradingTests(unittest.TestCase):
    def test_correct_remains_provisional_without_human(self):
        g=grade_submission(response(),manifest())
        self.assertTrue(g['deterministic_pass']); self.assertIsNone(g['successful_audit'])

    def test_human_finalizes(self):
        g=grade_submission(response(),manifest(),human())
        self.assertTrue(g['successful_audit']); self.assertEqual(g['status'],'adjudicated')

    def test_equivalent_formula(self):
        self.assertTrue(grade_submission(response('=SUM(I35,-I38)'),manifest(),human())['successful_audit'])

    def test_wrong_repair(self):
        self.assertFalse(grade_submission(response('=I35+I38'),manifest(),human())['successful_audit'])

    def test_hardcode_and_overfit_fail(self):
        for formula in ('=80','=I35-20'):
            with self.subTest(formula=formula):
                self.assertFalse(grade_submission(response(formula),manifest(),human())['successful_audit'])

    def test_unsupported_needs_review(self):
        g=grade_submission(response('=SUM(I35:I38)'),manifest())
        self.assertIn('repair:sign',g['pending_adjudication'])
        self.assertIsNone(g['successful_audit'])

    def test_evidence_required_for_override(self):
        adjudication=human(); adjudication['repair:sign']={'verdict':True,'evidence':''}
        g=grade_submission(response('=SUM(I35:I38)'),manifest(),adjudication)
        self.assertEqual(g['status'],'provisional')

    def test_human_cannot_override_proven_incorrect_repair(self):
        h=human(); h['repair:sign']={'verdict':True,'evidence':'Unsupported override attempt'}
        self.assertFalse(grade_submission(response('=80'),manifest(),h)['successful_audit'])

    def test_too_few_probes(self):
        m=manifest(); m['errors'][0]['probes']=m['errors'][0]['probes'][:1]
        self.assertIn('repair:sign',grade_submission(response(),m)['pending_adjudication'])

    def test_missed_error(self):
        g=grade_submission({'findings':[]},manifest(),human())
        self.assertFalse(g['successful_audit']); self.assertEqual(g['metrics']['root_cause_recall']['numerator'],0)

    def test_clean(self):
        m={'case_id':'clean','errors':[]}
        self.assertIsNone(grade_submission({'findings':[]},m)['successful_audit'])
        self.assertTrue(grade_submission({'findings':[]},m,human())['successful_audit'])
        self.assertFalse(grade_submission(response(),m,human())['successful_audit'])

    def test_false_positive(self):
        r=response(); extra=copy.deepcopy(r['findings'][0]); extra['cell']='I99'; r['findings'].append(extra)
        g=grade_submission(r,manifest(),human())
        self.assertFalse(g['successful_audit']); self.assertEqual(g['metrics']['finding_precision']['denominator'],2)

    def test_nonmaterial_suggestion_not_false_positive(self):
        r=response(); extra=copy.deepcopy(r['findings'][0]); extra.update(cell='I99',material=False);r['findings'].append(extra)
        self.assertTrue(grade_submission(r,manifest(),human())['successful_audit'])

    def test_duplicates_and_conflicting_duplicate(self):
        r=response();r['findings'].append(copy.deepcopy(r['findings'][0]))
        g=grade_submission(r,manifest(),human())
        self.assertTrue(g['successful_audit']);self.assertEqual(g['metrics']['finding_precision']['denominator'],1)
        r['findings'][1]['corrected_formula']='=I35+I38'
        self.assertFalse(grade_submission(r,manifest(),human())['successful_audit'])

    def test_wrong_magnitude_or_propagation(self):
        r=response();r['findings'][0]['original_minus_correct']=True
        self.assertFalse(grade_submission(r,manifest(),human())['successful_audit'])
        r=response();r['findings'][0]['downstream_cells']=[]
        g=grade_submission(r,manifest(),human())
        self.assertTrue(g['successful_audit']);self.assertEqual(g['metrics']['propagation_accuracy']['numerator'],0)

    def test_malformed_refused(self):
        for r in (None,[],{}, {'findings':[None]}, {'findings':[{}]}, {'findings':[],'status':'refused'}):
            with self.subTest(r=r):self.assertEqual(grade_submission(r,manifest())['status'],'invalid')

    def test_excel_lexical_syntax(self):
        self.assertEqual(evaluate_formula('=$I$35-I$38',{'I35':100,'I38':20})[0],80)
        for formula in ('=$$I35-I38','=I$3$5-I38','=0x50+I35','=1_000+I35'):
            with self.assertRaises(NeedsReview):evaluate_formula(formula,{'I35':100,'I38':20})

    def test_excel_exponent_precedence_routes_review(self):
        for formula in ('=-2^2','=2^3^2','=2**3'):
            with self.assertRaises(NeedsReview):evaluate_formula(formula,{})

    def test_invalid_adjudication_types(self):
        for item in ([1], {'criteria': []}, {'criteria': 'bad'}):
            with self.assertRaises(ValueError):grade_submission(response(),manifest(),item)

    def test_formula_safety(self):
        for formula in ('=__import__("os")','=I35/0','=2^100000','=SUM(A1:A2)','=True','=I35.__class__','=I35[0]'):
            with self.subTest(formula=formula):
                with self.assertRaises(NeedsReview):evaluate_formula(formula,{'I35':100})

    def test_bad_numeric_types_are_failures_not_crashes(self):
        for value in (True, float('nan'), float('inf'), '80', 10**2000, None):
            with self.subTest(type=type(value)):
                r=response();r['findings'][0]['correct_value']=value
                self.assertFalse(grade_submission(r,manifest(),human())['successful_audit'])

    def test_bad_dependency_types_route_to_review(self):
        for value in (True, float('nan'), float('inf'), '100', None):
            with self.subTest(value=value):
                with self.assertRaises(NeedsReview):evaluate_formula('=I35-20',{'I35':value})

    def test_huge_formula_bounded(self):
        with self.assertRaises(NeedsReview):evaluate_formula('='+'1+'*2000+'1',{})
        with self.assertRaises(NeedsReview):evaluate_formula('='+str(10**1000),{})

    def test_downstream_symptom_is_not_an_independent_false_positive(self):
        r=response();r['findings'].append({'sheet':'Cash Flow','cell':'I45','diagnosis':'Downstream total is overstated'})
        g=grade_submission(r,manifest(),human())
        self.assertTrue(g['successful_audit']); self.assertEqual(g['metrics']['finding_precision']['denominator'],1)
        r['findings'][-1]['corrected_formula']='=80'
        self.assertFalse(grade_submission(r,manifest(),human())['successful_audit'])

    def test_material_type_validation(self):
        r=response();r['findings'][0]['material']='false'
        self.assertEqual(grade_submission(r,manifest())['status'],'invalid')

    def test_diagnosis_human_failure(self):
        h=human();h['explanation:sign']['verdict']=False
        self.assertFalse(grade_submission(response(),manifest(),h)['successful_audit'])


class ActualManifestTests(unittest.TestCase):
    """Authoring QA against released manifests, not blind model performance."""
    def test_all_actual_manifests(self):
        root=Path(__file__).resolve().parents[1]
        wrong={'case-001':'=I35+I36-I37+I38','dev-002':'=G9*G19','dev-003':'=G11-G14-G15-G16-G17+G18'}
        for cid in ('case-001','dev-002','dev-003','dev-004'):
            with self.subTest(case=cid):
                m=json.loads((root/'references'/cid/'manifest.json').read_text())
                findings=[]
                for error in m['errors']:
                    impact=error['impact']
                    findings.append({'sheet':error['sheet'],'cell':error['cell'],
                        'diagnosis':error['diagnosis_required'],'corrected_formula':error['accepted_formula'],
                        'correct_value':impact['correct_value'],'original_minus_correct':impact['original_minus_correct'],
                        'downstream_cells':error['downstream_cells']})
                    values=[evaluate_formula(wrong[cid],p['cells'])[0] for p in error['probes']]
                    self.assertTrue(any(abs(v-p['expected'])>impact['tolerance'] for v,p in zip(values,error['probes'])))
                response={'findings':findings}
                self.assertTrue(grade_submission(response,m)['deterministic_pass'])
                self.assertIsNone(grade_submission(response,m)['successful_audit'])
                if findings:
                    findings[0]['corrected_formula']=wrong[cid]
                    self.assertFalse(grade_submission(response,m)['deterministic_pass'])

    def test_numeric_metric_counts_required_outputs(self):
        r=response();r['findings'][0]['original_minus_correct']=0
        metric=grade_submission(r,manifest())['metrics']['numerical_impact_accuracy']
        self.assertEqual(metric,{'numerator':1,'denominator':2})


if __name__=='__main__':unittest.main()
