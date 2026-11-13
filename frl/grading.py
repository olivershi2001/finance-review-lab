"""Conservative, dependency-free grading of proposed repairs; not an Excel engine.

Human verdicts use {criterion: {verdict: bool, evidence: nonempty str}}.
Supported criteria: detection:<id>, explanation:<id>, repair:<id>, restraint.
Only an evidence-bearing human adjudication can finalize an audit success.
"""
import ast
import math
import re

VERSION = '0.2.0'


class NeedsReview(ValueError):
    """Formula is outside the intentionally restricted evaluator."""


def evaluate_formula(formula, cells):
    """Evaluate arithmetic, cell refs and SUM/MIN/MAX/ABS; never eval source code."""
    if not isinstance(formula, str) or not formula.startswith('='):
        raise NeedsReview('A live formula beginning with = is required')
    source = formula[1:].strip()
    source = re.sub(r'(?<![A-Za-z0-9_$])\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)(?![A-Za-z0-9_$])', r'\1\2', source)
    if '$' in source or '_' in source or re.search(r'\b0[xXoObB]', source):
        raise NeedsReview('Unsupported numeric or cell-reference syntax')
    if '^' in source or '**' in source:
        raise NeedsReview('Exponentiation requires Excel precedence review')
    if len(source) > 2000 or re.search(r'[!\[\]:;"\'{}]', source):
        raise NeedsReview('Unsupported Excel syntax')
    try:
        tree = ast.parse(source.replace('^', '**'), mode='eval')
    except (SyntaxError, RecursionError) as exc:
        raise NeedsReview('Unsupported formula syntax') from exc
    if len(list(ast.walk(tree))) > 150:
        raise NeedsReview('Formula too complex')
    dependencies = set()
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name) and re.fullmatch(r'[A-Za-z]{1,3}[1-9][0-9]*', node.id):
            key = node.id.upper()
            if key not in cells:
                raise NeedsReview('Unspecified dependency: ' + key)
            if not _number(cells[key]):
                raise NeedsReview('Dependency is not a finite number: ' + key)
            dependencies.add(key)
            return cells[key]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
            if isinstance(node.op, ast.Pow) and abs(b) <= 10 and abs(a) <= 1e12: return a ** b
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            args = [visit(x) for x in node.args]
            name = node.func.id.upper()
            if name == 'SUM': return sum(args)
            if name == 'MIN' and args: return min(args)
            if name == 'MAX' and args: return max(args)
            if name == 'ABS' and len(args) == 1: return abs(args[0])
        raise NeedsReview('Unsupported operation')
    try:
        result = visit(tree.body)
        if type(result) not in (int, float) or not math.isfinite(result):
            raise NeedsReview('Non-finite result')
    except (ArithmeticError, OverflowError, TypeError, RecursionError) as exc:
        raise NeedsReview('Formula cannot be evaluated safely') from exc
    return result, dependencies


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _close(actual, expected, tolerance):
    return _number(actual) and _number(expected) and abs(actual - expected) <= tolerance


def _human(adjudication, key):
    entry = adjudication.get(key)
    if isinstance(entry, dict) and type(entry.get('verdict')) is bool and isinstance(entry.get('evidence'), str) and entry['evidence'].strip():
        return entry['verdict']
    return None


def validate_submission(response):
    """Return errors rather than silently dropping malformed findings."""
    if not isinstance(response, dict): return ['Response must be a JSON object']
    if not isinstance(response.get('findings'), list): return ['findings must be a list']
    errors = []
    for i, finding in enumerate(response['findings']):
        if not isinstance(finding, dict):
            errors.append(f'Finding {i} must be an object'); continue
        if 'material' in finding and type(finding['material']) is not bool:
            errors.append(f'Finding {i} material must be boolean')
        for field in ('sheet', 'cell', 'diagnosis'):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                errors.append(f'Finding {i} missing {field}')
        if not isinstance(finding.get('downstream_cells', []), list) or any(not isinstance(x, str) for x in finding.get('downstream_cells', [])):
            errors.append(f'Finding {i} invalid downstream_cells')
    return errors


def grade_submission(response, manifest, adjudication=None):
    """Return JSON-safe criterion evidence and conservative provisional metrics.

    manifest errors need >=3 probes (base + two perturbations) for automated
    formula acceptance. Missing probe evidence routes repairs to human review.
    adjudication may be {'criteria': {...}} or the criterion mapping itself.
    """
    adjudication = {} if adjudication is None else adjudication
    if not isinstance(adjudication, dict):
        raise ValueError('Adjudication must be an object')
    adjudication = adjudication.get('criteria', adjudication)
    if not isinstance(adjudication, dict):
        raise ValueError('Adjudication criteria must be an object')
    errors = manifest.get('errors', [])
    result = {'grader_version': VERSION, 'case_id': manifest['case_id'], 'status': 'provisional',
              'successful_audit': None, 'deterministic_pass': False, 'criteria': [], 'issues': [], 'metrics': {}}
    invalid = validate_submission(response)
    if invalid or response.get('status') in ('refused', 'incomplete', 'missing'):
        result.update(status='invalid', successful_audit=False, issues=invalid or [response['status']])
        return result
    findings = response['findings']
    # Duplicate location findings do not boost recall or precision, but conflicting
    # repairs remain a failure rather than hiding behind the first correct repair.
    groups = {}
    for f in findings:
        key = (f['sheet'].strip().casefold(), f['cell'].strip().replace('$', '').upper())
        groups.setdefault(key, []).append(f)
    reference_locations = {(e['sheet'].casefold(), e['cell'].replace('$', '').upper()) for e in errors}
    symptom_locations = set()
    for e in errors:
        for location in e.get('downstream_cells', []):
            sheet, cell = location.rsplit('!', 1) if '!' in location else (e['sheet'], location)
            symptom_locations.add((sheet.strip("'").casefold(), cell.replace('$', '').upper()))
    extras = [key for key, fs in groups.items() if key not in reference_locations
              and any(f.get('material', True) is not False and
                      (key not in symptom_locations or bool(f.get('corrected_formula'))) for f in fs)]
    detected = repaired = numerical = propagated = numerical_outputs = 0
    deterministic = not extras
    pending = []
    human_all = True
    for error in errors:
        eid = error['id']
        fs = groups.get((error['sheet'].casefold(), error['cell'].replace('$', '').upper()), [])
        detection = _human(adjudication, 'detection:' + eid)
        explanation = _human(adjudication, 'explanation:' + eid)
        if detection is None: pending.append('detection:' + eid)
        if explanation is None: pending.append('explanation:' + eid)
        detected += int(bool(fs) and detection is not False)
        record = {'id': eid, 'matched_findings': len(fs), 'detection': detection, 'explanation': explanation,
                  'repair': False, 'numerical': False, 'propagation': False, 'formula_evidence': []}
        candidates = []
        for finding in fs:
            formula = finding.get('corrected_formula')
            probes = error.get('probes', [])
            tolerance = error.get('impact', {}).get('tolerance', 1e-6)
            repair = None
            evidence = []
            if not isinstance(formula, str) or not formula.startswith('='):
                repair = False
            else:
                try:
                    evaluations = [evaluate_formula(formula, p['cells']) for p in probes]
                    # A constant "formula" is never a valid model repair.
                    if evaluations and any(not deps for _, deps in evaluations): repair = False
                    elif len(probes) < 3: repair = None
                    else: repair = all(_close(value, p['expected'], tolerance) for (value, _), p in zip(evaluations, probes))
                    evidence = [{'actual': v, 'expected': p['expected'], 'dependencies': sorted(d)} for (v, d), p in zip(evaluations, probes)]
                except NeedsReview as exc:
                    evidence = [{'needs_review': str(exc)}]
            override = _human(adjudication, 'repair:' + eid)
            if override is False or (repair is None and override is True): repair = override
            if repair is None: pending.append('repair:' + eid)
            impact = error.get('impact', {})
            numeric_checks = (_close(finding.get('correct_value', finding.get('correct_fcf')), impact.get('correct_value'), tolerance),
                              _close(finding.get('original_minus_correct', finding.get('original_minus_correct_fcf')), impact.get('original_minus_correct'), tolerance))
            nums = all(numeric_checks)
            prop = set(finding.get('downstream_cells', [])) == set(error.get('downstream_cells', []))
            candidates.append((repair, nums, prop, numeric_checks))
            record['formula_evidence'].append(evidence)
        record['repair'] = all(c[0] is True for c in candidates) if candidates else False
        record['numerical'] = all(c[1] for c in candidates) if candidates else False
        record['propagation'] = all(c[2] for c in candidates) if candidates else False
        repaired += int(record['repair']); numerical += int(record['numerical']); propagated += int(record['propagation'])
        numerical_outputs += sum(int(all(c[3][i] for c in candidates)) for i in range(2)) if candidates else 0
        deterministic &= bool(fs) and record['repair'] and record['numerical']
        human_all &= detection is True and explanation is True
        result['criteria'].append(record)
    restraint = _human(adjudication, 'restraint')
    if restraint is None: pending.append('restraint')
    human_all &= restraint is True
    result['deterministic_pass'] = bool(deterministic)
    result['issues'] = ['Unmatched material finding: ' + str(x) for x in extras]
    result['pending_adjudication'] = sorted(set(pending))
    result['restraint'] = restraint
    count = len(errors)
    result['metrics'] = {'root_cause_recall': {'numerator': detected, 'denominator': count, 'provisional': True},
                         'finding_precision': {'numerator': detected, 'denominator': len(reference_locations.intersection(groups)) + len(extras), 'provisional': True},
                         'valid_repair_rate': {'numerator': repaired, 'denominator': count},
                         'numerical_impact_accuracy': {'numerator': numerical_outputs, 'denominator': 2 * count},
                         'propagation_accuracy': {'numerator': propagated, 'denominator': count},
                         'clean_case_pass': None if count else bool(not extras and restraint is True)}
    if not pending:
        result['status'] = 'adjudicated'
        result['successful_audit'] = bool(deterministic and human_all)
    return result
