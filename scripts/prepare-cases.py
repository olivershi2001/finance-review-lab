"""Prepare public reference manifests and add Excel print metadata. No packages needed."""
from pathlib import Path
import hashlib,json,zipfile
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
E.register_namespace('',NS)
def tag(s):return '{'+NS+'}'+s
def save(p,data):p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def print_settings(file):
    with zipfile.ZipFile(file) as z:parts={n:z.read(n) for n in z.namelist()}
    workbook=E.fromstring(parts['xl/workbook.xml'])
    sheets=workbook.find(tag('sheets'));names=workbook.find(tag('definedNames'))
    if names is None:
        names=E.Element(tag('definedNames'));at=next((j for j,x in enumerate(workbook) if x.tag==tag('calcPr')),len(workbook));workbook.insert(at,names)
    for x in list(names):
        if x.attrib.get('name') in ('_xlnm.Print_Area','_xlnm.Print_Titles'):names.remove(x)
    for i,sheet in enumerate(sheets):
        entry=f'xl/worksheets/sheet{i+1}.xml';root=E.fromstring(parts[entry])
        pr=root.find(tag('sheetPr'))
        if pr is None:pr=E.Element(tag('sheetPr'));root.insert(0,pr)
        setup=pr.find(tag('pageSetUpPr'))
        if setup is None:setup=E.SubElement(pr,tag('pageSetUpPr'))
        setup.set('fitToPage','1')
        for name in ['pageMargins','pageSetup']:
            element=root.find(tag(name))
            if element is not None:root.remove(element)
        later={'headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst'}
        at=next((j for j,x in enumerate(root) if x.tag.split('}')[-1] in later),len(root))
        root.insert(at,E.Element(tag('pageMargins'),dict(left='.25',right='.25',top='.35',bottom='.35',header='.15',footer='.15')))
        root.insert(at+1,E.Element(tag('pageSetup'),dict(paperSize='9',orientation='landscape',fitToWidth='1',fitToHeight='0')))
        parts[entry]=E.tostring(root,encoding='utf-8',xml_declaration=True)
        wide=file.parent.name=='case-001';right='L' if wide else 'I';bottom=49 if wide else 37
        name=sheet.attrib['name']
        E.SubElement(names,tag('definedName'),dict(name='_xlnm.Print_Area',localSheetId=str(i))).text=f"'{name}'!$C$2:${right}${bottom}"
        E.SubElement(names,tag('definedName'),dict(name='_xlnm.Print_Titles',localSheetId=str(i))).text=f"'{name}'!$1:$6"
    parts['xl/workbook.xml']=E.tostring(workbook,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
def probe(cells,expected):return {'cells':cells,'expected':expected}
def manifest(case,category,sheet,cell,formula,bad,probes,correct,impact,downstream,diagnosis):
    return {'case_id':case,'version':'0.2.0','split':'public_dev','category':category,'source_type':'original_synthetic',
            'units':'USD millions except explicitly labeled ratios and per-share values','errors': [] if not cell else [
                {'id':'root-1','sheet':sheet,'cell':cell,'diagnosis_required':diagnosis,'accepted_formula':formula,
                 'existing_formula':bad,'probes':probes,'impact':{'correct_value':correct,'original_minus_correct':impact,'tolerance':.0001},'downstream_cells':downstream}]}

def main():
    e=json.loads((ROOT/'references/case-001/expected.json').read_text())[1]
    originals=[]
    with zipfile.ZipFile(ROOT/'references/case-001/reference.xlsx') as z:
        root=E.fromstring(z.read('xl/worksheets/sheet1.xml'))
        cells={c.attrib['r']:c for c in root.findall('.//'+tag('c'))}
        original={c:float(cells[c].find(tag('v')).text) for c in ['I35','I36','I37','I38']}
    p1=probe(original,e['fcf']);p2=probe({'I35':10,'I36':2,'I37':4,'I38':-3},11);p3=probe({'I35':22,'I36':4,'I37':8,'I38':0},18)
    cases=[manifest('case-001','operating_cash_flow','Operating Model','I39','=I35+I36-I37-I38','=SUM(I35:I36)-I37+I38',[p1,p2,p3],e['fcf'],2*e['delta'],['Operating Model!I40']+[f'Operating Model!{c}42' for c in 'IJKL'],'Increase in working capital is added instead of deducted.'),
      manifest('dev-002','debt_interest','Debt Schedule','G20','=G17*G19','=G9*G19',[
          probe({'G9':135,'G13':95,'G17':115,'G19':.09},10.35),
          probe({'G9':150,'G13':150,'G17':150,'G19':.06},9),
          probe({'G9':80,'G13':120,'G17':100,'G19':.1},10)],10.35,1.8,['Debt Schedule!G22']+[f'Debt Schedule!{c}24' for c in 'GHI'],'Opening debt used rather than the specified arithmetic average debt balance.'),
      manifest('dev-003','enterprise_equity','Valuation','G21','=G11-G14-G15-G16+G17+G18','=G11-SUM(G14:G16)-G17+G18',[
          probe({'G11':484.5,'G14':125,'G15':20,'G16':17,'G17':38,'G18':9},369.5),
          probe({'G11':400,'G14':100,'G15':0,'G16':10,'G17':0,'G18':5},295),
          probe({'G11':300,'G14':90,'G15':15,'G16':5,'G17':50,'G18':0},240)],369.5,-76,['Valuation!G24'],'Excess cash subtracted rather than added in the enterprise-to-equity bridge.'),
      manifest('dev-004','operating_cash_flow','Operating Model',None,None,None,[],None,None,[],None)]
    for case in cases:
        cid=case['case_id'];folder=ROOT/'cases'/cid;ref=ROOT/'references'/cid
        for f in [folder/'model.xlsx',ref/'reference.xlsx']:print_settings(f)
        case['model_sha256']=sha(folder/'model.xlsx');case['reference_sha256']=sha(ref/'reference.xlsx')
        save(ref/'manifest.json',case)
        save(folder/'metadata.json',{'case_id':cid,'version':case['version'],'split':'public_dev','category':case['category'],'units':case['units'],'model_sha256':case['model_sha256']})
        save(ref/'error-manifest.json',{'case_id':cid,'errors':case['errors']})
        rubric={'primary':'All root causes detected, valid live repairs, correct numerical impact, and no material false corrections.',
                'human_review_required':['detection','explanation','restraint'],'propagation':'Secondary; list precise downstream outputs and do not misclassify unaffected periods.',
                'numeric_tolerance':.0001,'formula_equivalence':'Base plus two perturbations; unsupported syntax needs evidenced human review.',
                'errors':case['errors'],'clean_case':not case['errors']}
        save(ref/'rubric.json',rubric)
        if cid!='case-001':
            text=f"# {cid} answer key\n\nReference-only public development material. Do not give to evaluation sessions.\n\n"
            if case['errors']:
                err=case['errors'][0];text+=f"Root: `{err['sheet']}!{err['cell']}`. {err['diagnosis_required']}\n\nCorrect formula: `{err['accepted_formula']}`. Equivalent formulas are accepted after execution checks or human review.\n\nCorrect output: {err['impact']['correct_value']} USD millions. Original minus correct: {err['impact']['original_minus_correct']} USD millions.\n\nDownstream: "+', '.join(err['downstream_cells'])+'.\n'
            else:text+='There are no material formula errors. The revenue contraction releases working capital, and the expansion capex creates a legitimate negative cash-flow year. Do not change authoritative assumptions. A successful response leaves the formulas unchanged.\n'
            text+='\nSee rubric.json for grading criteria and expected.json for reference outputs. This is a development example, not a private test or measured AI result.\n'
            (ref/'answer-key.md').write_text(text)
    print('Prepared four public manifests, metadata, rubrics, and print settings.')
if __name__=='__main__':main()
