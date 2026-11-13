"""Check exported XLSX caches against independent Decimal finance calculations."""
from decimal import Decimal as D
from pathlib import Path
import json, zipfile, xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parent
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def read(path):
    with zipfile.ZipFile(path) as z:
        parts={n:z.read(n) for n in z.namelist()}
    sheets=[]
    for i in range(1,4):
        root=E.fromstring(parts[f'xl/worksheets/sheet{i}.xml'])
        cells={x.attrib['r']:x for x in root.findall('.//s:sheetData/s:row/s:c',NS)}
        for cell in cells.values():assert cell.attrib.get('t')!='e',f'Excel error: {cell.attrib}'
        pane=root.find('s:sheetViews/s:sheetView/s:pane',NS)
        assert pane.attrib['xSplit']=='4' and pane.attrib['ySplit']=='6'
        assert root.find('s:sheetViews/s:sheetView',NS).attrib['showGridLines']=='0'
        assert root.find('s:pageSetup',NS).attrib['orientation']=='landscape'
        assert root.find('s:pageSetup',NS).attrib['fitToWidth']=='1'
        sheets.append(cells)
    assert not any(n.startswith('xl/externalLinks/') for n in parts)
    assert len(E.fromstring(parts['xl/workbook.xml']).findall('s:definedNames/s:definedName',NS))>=6
    return parts,sheets
def number(cells,cell): return D(cells[cell].find('s:v',NS).text)
def close(actual,expected):assert abs(actual-expected)<D('.00000001'),(actual,expected)

def main():
    rp,rs=read(ROOT/'references/case-001/reference.xlsx')
    ap,aus=read(ROOT/'cases/case-001/model.xlsx')
    assert rp['xl/styles.xml']==ap['xl/styles.xml'],'Styles differ'
    differences=[]
    for i,(r,a) in enumerate(zip(rs,aus)):
        assert r.keys()==a.keys()
        for addr in r:
            assert r[addr].attrib.get('s')==a[addr].attrib.get('s'),f'Style change {addr}'
            rf=r[addr].findtext('s:f',default='',namespaces=NS)
            af=a[addr].findtext('s:f',default='',namespaces=NS)
            if rf!=af:differences.append((i+1,addr))
            if not rf: assert E.tostring(r[addr])==E.tostring(a[addr]),f'Input change {addr}'
    assert differences==[(1,'I39')],differences
    # Inputs are separately transcribed scenario values, not formula-engine results.
    rev=D('126');prior_nwc=D('20.5'); cumulative=D(0); expected=[]
    for c,g,gm,op,ar in zip('HIJKL',['.10','.09','.08','.07','.06'],['.42','.425','.43','.435','.44'],['.22','.218','.216','.214','.212'],['.145','.147','.148','.148','.148']):
        rev*=1+D(g);ebitda=rev*(D(gm)-D(op));da=rev*D('.03');ebit=ebitda-da
        tax=max(ebit,D(0))*D('.25');nwc=rev*(D(ar)+D('.10')-D('.08'));delta=nwc-prior_nwc
        capex=rev*D('.045');fcf=ebit-tax+da-capex-delta;cumulative+=fcf
        for row,v in {9:rev,17:ebitda,20:da,21:ebit,24:tax,31:nwc,32:delta,37:capex,39:fcf,42:cumulative}.items():close(number(rs[0],f'{c}{row}'),v)
        expected.append((c,fcf,delta,cumulative));prior_nwc=nwc
    impact=2*expected[1][2]
    for c,fcf,delta,cum in expected:
        close(number(aus[0],f'{c}39'),fcf+(impact if c=='I' else 0))
        close(number(aus[0],f'{c}42'),cum+(impact if c>='I' else 0))
    for sheets in [rs,aus]:
        for c in 'EFGHIJKL':
            for row in range(10,14):close(number(sheets[2],f'{c}{row}'),D(0))
    report={'status':'passed','forecast_numeric_assertions':60,'formula_changes':[{'sheet':'Operating Model','cell':'I39'}],
            'styles_identical':True,'inputs_identical':True,'checks_pass_in_both':True,
            'native_excel_tested':False,'correct_2027_fcf':str(expected[1][1]),'overstatement':str(impact)}
    print(json.dumps(report,indent=2))
    (ROOT/'references/case-001/validation.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
