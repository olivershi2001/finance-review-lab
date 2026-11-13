"""Compare disposable, natively recalculated XLSX copies with shipped workbooks.

Run only after opening each copy in Excel, Calculate Now, and saving it.
This checks saved evidence; it does not automate or attest to those UI actions.
"""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
sys.path.insert(0, str(ROOT))
from verify_suite import read


def canonical_formula(value):
    # Excel removes optional quotes from simple sheet names on save.
    return re.sub(r"'([A-Za-z_][A-Za-z0-9_]*)'!", r'\1!', value)


def coordinate(address):
    column, row = re.fullmatch(r'([A-Z]+)([0-9]+)', address).groups()
    number = 0
    for char in column:
        number = number*26 + ord(char)-64
    return number, int(row)


def translate_shared(formula, origin, target):
    x, y = coordinate(origin)
    tx, ty = coordinate(target)
    def move(match):
        fixed_col, col, fixed_row, row = match.groups()
        nx, ny = coordinate(col+row)
        nx += 0 if fixed_col else tx-x
        ny += 0 if fixed_row else ty-y
        assert nx > 0 and ny > 0, 'Invalid shared formula reference'
        label = ''
        while nx:
            nx, rem = divmod(nx-1, 26)
            label = chr(65+rem)+label
        return fixed_col+label+fixed_row+str(ny)
    # Skip string constants and quoted sheet names. This suite uses scalar A1 refs.
    tokens = re.split(r'("(?:[^"]|"")*"|\'(?:[^\']|\'\')*\')', formula)
    for index in range(0, len(tokens), 2):
        tokens[index] = re.sub(r'(?<![A-Za-z0-9_])(\$?)([A-Z]{1,3})(\$?)([1-9][0-9]*)(?![A-Za-z0-9_(])', move, tokens[index])
    return ''.join(tokens)


def formulas(cells):
    anchors = {}
    for address, cell in cells.items():
        f = cell.find('s:f', NS)
        if f is not None and f.get('t') == 'shared' and f.text:
            anchors[f.get('si')] = (address, f.text)
    result = {}
    for address, cell in cells.items():
        f = cell.find('s:f', NS)
        value = '' if f is None else (f.text or '')
        if f is not None and f.get('t') == 'shared' and not value:
            origin, base = anchors[f.get('si')]
            value = translate_shared(base, origin, address)
        result[address] = value
    return result


def values(parts, sheets):
    strings = []
    if 'xl/sharedStrings.xml' in parts:
        root = ET.fromstring(parts['xl/sharedStrings.xml'])
        strings = [''.join(x.itertext()) for x in root.findall('s:si', NS)]
    result = {}
    for sheet, cells in sheets.items():
        for address, cell in cells.items():
            kind = cell.get('t')
            assert kind != 'e', f'Cached Excel error at {sheet}!{address}'
            value = cell.findtext('s:v', namespaces=NS)
            if kind == 's':
                value = strings[int(value)]
            elif kind == 'inlineStr':
                value = ''.join(cell.find('s:is', NS).itertext())
            elif value is not None and kind not in ('str', 'b'):
                try:
                    value = Decimal(value)
                except InvalidOperation:
                    raise AssertionError(f'Invalid numeric value at {sheet}!{address}')
            result[sheet, address] = value
    return result


def compare(source, native):
    sp, ss, _ = read(source)
    np, ns, _ = read(native)
    assert ss.keys() == ns.keys(), 'Sheet names/order changed'
    sv, nv = values(sp, ss), values(np, ns)
    count = 0
    for sheet, cells in ss.items():
        sf, nform = formulas(cells), formulas(ns[sheet])
        for address, cell in cells.items():
            f = sf[address]
            other = ns[sheet].get(address)
            assert other is not None or (not f and sv[sheet, address] is None), f'Missing cell {sheet}!{address}'
            if other is None:
                continue
            nf = nform[address]
            assert canonical_formula(f) == canonical_formula(nf), f'Formula changed {sheet}!{address}: {f} -> {nf}'
            a, b = sv[sheet, address], nv[sheet, address]
            if isinstance(a, Decimal):
                assert isinstance(b, Decimal) and a.is_finite() and b.is_finite() and abs(a-b) < Decimal('1e-8'), f'Value changed {sheet}!{address}: {a} -> {b}'
            else:
                assert a == b, f'Text/input changed {sheet}!{address}: {a!r} -> {b!r}'
            if f:
                assert a is not None, f'Missing formula cache {sheet}!{address}'
                count += 1
    return {'formula_caches_compared': count, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'native_saved_sha256': hashlib.sha256(native.read_bytes()).hexdigest(), 'status': 'passed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = []
    for cid in ('case-001', 'dev-002', 'dev-003', 'dev-004'):
        for kind, name in (('cases', 'model.xlsx'), ('references', 'reference.xlsx')):
            filename = f'{cid}-{kind}.xlsx'
            if cid == 'dev-002' and kind == 'references':
                filename = 'dev-002-reference-native-base.xlsx'
            result = compare(ROOT/kind/cid/name, args.native_directory/filename)
            results.append({'case_id': cid, 'version': kind, **result})
    parts, sheets, _ = read(args.native_directory/'dev-002-zero-rate-native.xlsx')
    boundary = values(parts, sheets)
    assert boundary['Assumptions', 'G14'] == Decimal(0)
    assert boundary['Debt Schedule', 'G20'] == Decimal(0)
    assert boundary['Debt Schedule', 'G22'] == 'n.a.'
    report = {'status': 'passed', 'workbooks_compared': len(results),
              'formula_caches_compared': sum(r['formula_caches_compared'] for r in results),
              'evidence_scope': 'Disposable copies recalculated and saved through native Microsoft Excel UI; source files unchanged.',
              'formula_normalization': 'Expand native shared A1 formulas; remove optional quotes around simple sheet names.',
              'numeric_absolute_tolerance': '1e-8', 'results': results,
              'input_change_test': {'case_id': 'dev-002', 'version': 'reference',
                                   'source_sha256': hashlib.sha256((ROOT/'references/dev-002/reference.xlsx').read_bytes()).hexdigest(),
                                   'input': 'Assumptions!G14 = 0', 'interest': 'Debt Schedule!G20 = 0',
                                   'coverage': 'Debt Schedule!G22 = n.a.', 'status': 'passed',
                                   'native_saved_sha256': hashlib.sha256((args.native_directory/'dev-002-zero-rate-native.xlsx').read_bytes()).hexdigest()},
              'limitations': ['One native input boundary tested; other perturbations tested in the authoring engine.',
                              'Printed-page appearance is not established by these cache comparisons.',
                              'Saved files alone do not independently prove the recorded UI actions.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'workbooks_compared':len(results), 'formula_caches_compared':report['formula_caches_compared']}))


if __name__ == '__main__':
    main()
