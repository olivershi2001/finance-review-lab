"""Independent Decimal validation of the four public workbooks and case isolation."""
from decimal import Decimal as D
from pathlib import Path
import hashlib,json,re,zipfile
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parent
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with zipfile.ZipFile(p) as z:parts={n:z.read(n) for n in z.namelist()}
    wb=E.fromstring(parts['xl/workbook.xml']);names=[x.attrib['name'] for x in wb.findall('s:sheets/s:sheet',NS)]
    sheets={};roots={}
    for i,name in enumerate(names):
        root=E.fromstring(parts[f'xl/worksheets/sheet{i+1}.xml']);roots[name]=root
        sheets[name]={c.attrib['r']:c for c in root.findall('.//s:sheetData/s:row/s:c',NS)}
    return parts,sheets,roots
def n(cells,c):return D(cells[c].findtext('s:v',namespaces=NS))
def close(a,b):assert abs(a-b)<D('.00000001'),f'{a} != {b}'
def calc_debt():
    out={};opening=D(180);cum=D(0)
    for c,borrow,pay,rate,eb in zip('EFGHI',[20,0,0,0,0],[30,35,40,45,50],['.08','.085','.09','.085','.08'],[42,44,46,48,50]):
        closing=opening+D(borrow)-D(pay);avg=(opening+closing)/2;interest=avg*D(rate);cum+=interest
        out.update({c+'9':opening,c+'13':closing,c+'17':avg,c+'20':interest,c+'22':D(eb)/interest,c+'24':cum,c+'27':D(0)});opening=closing
    return out
def calc_valuation():
    out={}
    for c,eb,multiple,debt,nci,cash,invest,shares in zip('EFGHI',[48,52,57,61,66],['8','8.25','8.5','8.5','8.75'],[150,140,125,110,95],[15,16,17,18,19],[25,30,38,45,52],[8,8,9,9,10],[40,41,42,43,44]):
        ev=D(eb)*D(multiple);eq=ev-D(debt)-20-D(nci)+D(cash)+D(invest)
        out.update({c+'11':ev,c+'21':eq,c+'24':eq/D(shares)})
    return out
def calc_control():
    out={};revenue=D(90);prior=D('16.2');cum=D(0)
    for c,growth,margin,capex_ratio in zip('EFGHI',['.08','-.12','.06','.07','.05'],['.19','.17','.18','.19','.20'],['.05','.25','.05','.05','.05']):
        revenue*=1+D(growth);eb=revenue*D(margin);da=revenue*D('.035');ebit=eb-da;tax=max(D(0),ebit)*D('.25');nwc=revenue*D('.18');change=nwc-prior;capex=revenue*D(capex_ratio);fcf=ebit-tax+da-capex-change;cum+=fcf
        out.update({c+'9':revenue,c+'12':eb,c+'15':da,c+'16':ebit,c+'17':tax,c+'21':nwc,c+'22':change,c+'27':capex,c+'30':fcf,c+'33':cum});prior=nwc
    assert out['F22']<0 and out['F30']<0
    return out
def calc_original():
    out={};revenue=D('126');prior=D('20.5');cumulative=D(0)
    for c,g,gm,op,ar in zip('HIJKL',['.10','.09','.08','.07','.06'],['.42','.425','.43','.435','.44'],['.22','.218','.216','.214','.212'],['.145','.147','.148','.148','.148']):
        revenue*=1+D(g);ebitda=revenue*(D(gm)-D(op));da=revenue*D('.03');ebit=ebitda-da;tax=max(D(0),ebit)*D('.25');nwc=revenue*(D(ar)+D('.10')-D('.08'));change=nwc-prior;capex=revenue*D('.045');fcf=ebit-tax+da-capex-change;cumulative+=fcf
        out.update({c+'9':revenue,c+'17':ebitda,c+'20':da,c+'21':ebit,c+'24':tax,c+'31':nwc,c+'32':change,c+'37':capex,c+'39':fcf,c+'42':cumulative});prior=nwc
    return out
def acyclic(sheets):
    graph={}
    for sheet,cells in sheets.items():
        for addr,cell in cells.items():
            f=cell.findtext('s:f',default='',namespaces=NS)
            if not f:continue
            deps=[]
            # The authored suite uses scalar refs and simple same-sheet ranges.
            pattern=r"(?:'([^']+)'!|([A-Za-z_][A-Za-z_ ]*)!)?(\$?[A-Z]{1,3}\$?[1-9][0-9]*)(?::(\$?[A-Z]{1,3}\$?[1-9][0-9]*))?"
            for match in re.finditer(pattern,f):
                target=match[1] or match[2] or sheet;start=match[3].replace('$','');end=(match[4] or start).replace('$','')
                def coord(x):
                    l,r=re.fullmatch(r'([A-Z]+)([0-9]+)',x).groups();v=0
                    for ch in l:v=v*26+ord(ch)-64
                    return v,int(r)
                c1,r1=coord(start);c2,r2=coord(end)
                for cc in range(c1,c2+1):
                    label='';q=cc
                    while q:q,rem=divmod(q-1,26);label=chr(65+rem)+label
                    for rr in range(r1,r2+1):deps.append((target,label+str(rr)))
            graph[(sheet,addr)]=deps
    visited=set();active=set()
    def visit(node):
        assert node not in active,f'Circular reference {node}'
        if node in visited:return
        active.add(node)
        for dep in graph.get(node,[]):visit(dep)
        active.remove(node);visited.add(node)
    for node in graph:visit(node)
    return len(graph)
def verify(cid,expected):
    ref=ROOT/'references'/cid;blind=ROOT/'cases'/cid;manifest=json.loads((ref/'manifest.json').read_text())
    rp,rs,rr=read(ref/'reference.xlsx');ap,ass,ar=read(blind/'model.xlsx')
    assert sha(ref/'reference.xlsx')==manifest['reference_sha256']
    assert sha(blind/'model.xlsx')==manifest['model_sha256']
    assert rp['xl/styles.xml']==ap['xl/styles.xml']
    assert rs.keys()==ass.keys()
    changes=[];cached_differences=[]
    for name,cells in rs.items():
        assert cells.keys()==ass[name].keys()
        for address,cell in cells.items():
            other=ass[name][address]
            assert cell.attrib.get('s')==other.attrib.get('s'),f'Style difference {name}!{address}'
            f=cell.findtext('s:f',default='',namespaces=NS);of=other.findtext('s:f',default='',namespaces=NS)
            if f!=of:changes.append(name+'!'+address)
            if not f:assert E.tostring(cell)==E.tostring(other),f'Input difference {address}'
            if cell.findtext('s:v',default='',namespaces=NS)!=other.findtext('s:v',default='',namespaces=NS):cached_differences.append(name+'!'+address)
    intended=[e['sheet']+'!'+e['cell'] for e in manifest['errors']]
    assert changes==intended,(changes,intended)
    permitted=set(intended+[a for e in manifest['errors'] for a in e['downstream_cells']])
    assert set(cached_differences)<=permitted,(cached_differences,permitted)
    if intended:assert set(cached_differences)==permitted
    for parts,sheets,roots in [(rp,rs,rr),(ap,ass,ar)]:
        assert not any(x.startswith('xl/externalLinks/') or 'comments' in x.lower() for x in parts)
        for name,cells in sheets.items():
            for address,cell in cells.items():assert cell.attrib.get('t')!='e',f'Excel error {name}!{address}'
            pane=roots[name].find('s:sheetViews/s:sheetView/s:pane',NS)
            assert pane is not None and pane.attrib.get('xSplit')=='4' and pane.attrib.get('ySplit')=='6'
            assert roots[name].find('s:sheetViews/s:sheetView',NS).attrib['showGridLines']=='0'
            assert roots[name].find('s:pageSetup',NS).attrib['orientation']=='landscape'
            assert roots[name].find('s:pageSetup',NS).attrib['fitToWidth']=='1'
        acyclic(sheets)
    main=manifest['errors'][0]['sheet'] if manifest['errors'] else 'Operating Model'
    for cell,value in expected.items():close(n(rs[main],cell),value)
    for error in manifest['errors']:
        close(n(rs[error['sheet']],error['cell']),D(str(error['impact']['correct_value'])))
        close(n(ass[error['sheet']],error['cell'])-n(rs[error['sheet']],error['cell']),D(str(error['impact']['original_minus_correct'])))
    report={'case_id':cid,'status':'passed','independent_decimal_outputs':len(expected),'formula_changes':changes,'cached_outputs_changed':cached_differences,
            'identical_styles':True,'identical_inputs':True,'acyclic':True,'formula_error_scan':'no cached errors','print_and_panes_checked':True,
            'native_excel_verified':False,'visual_review':'recorded separately in suite QA log','reference_sha256':sha(ref/'reference.xlsx'),'model_sha256':sha(blind/'model.xlsx')}
    (ref/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
def main():
    # Original case has its own independent Decimal verifier.
    import verify_case
    verify_case.main()
    reports=[]
    for cid,expected in [('dev-002',calc_debt()),('dev-003',calc_valuation()),('dev-004',calc_control())]:reports.append(verify(cid,expected))
    reports.append(verify('case-001',calc_original()))
    print(json.dumps({'status':'passed','cases':4,'independent_decimal_outputs':sum(r['independent_decimal_outputs'] for r in reports),'native_excel_verified':False},indent=2))
if __name__=='__main__':main()
