import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const previews=process.env.FRL_PREVIEW_DIR || path.join(root,'build-previews');
await fs.mkdir(previews,{recursive:true});
const wb=Workbook.create();
const model=wb.worksheets.add('Operating Model'), inputs=wb.worksheets.add('Assumptions'), checks=wb.worksheets.add('Checks');
const cols=['E','F','G','H','I','J','K','L'];
const num='#,##0.0;(#,##0.0);"–"';
const money='$' + num;
const val=(s,a,v)=>s.getRange(a).values=[[v]];
const formula=(s,a,f)=>{s.getRange(a).formulas=[[f]];s.getRange(a).format.font.color=f.includes('!')?'#008000':'#000000';};
function section(s,r,label){val(s,`C${r}`,label);s.getRange(`C${r}:L${r}`).format={fill:'#233D59',font:{bold:true,color:'#FFFFFF'}};}
function total(s,r,currency=false){s.getRange(`C${r}:L${r}`).format.font.bold=true;s.getRange(`E${r}:L${r}`).format.borders={top:{style:'thin',color:'#9AA8B5'}};if(currency)s.getRange(`E${r}:L${r}`).setNumberFormat(money);}
for(const s of [model,inputs,checks]){
 s.showGridLines=false;s.getRange('A1:M49').format.font={name:'Arial',size:10,color:'#000000'};
 s.getRange('A1:B49').format.columnWidth=2;s.getRange('C1:C49').format.columnWidth=36;s.getRange('D1:D49').format.columnWidth=3;
 s.getRange('E1:L49').format.columnWidth=13;s.getRange('A1:M49').format.rowHeight=19;
 s.getRange('E7:L46').setNumberFormat(num);s.getRange('E1:L49').format.horizontalAlignment='right';
 val(s,'C2','Cedar Industrial Supply');s.getRange('C2:L2').format.font={size:14,bold:true};
 val(s,'C3','USD millions. Calendar years ended December 31.');s.getRange('C3:L3').format.font.italic=true;
 cols.forEach((c,i)=>{val(s,c+'5',2023+i);val(s,c+'6',i<3?'Actual':'Forecast');});
 s.getRange('E5:G6').format.fill='#E7EBEF';s.getRange('H5:L6').format.fill='#DCE7F2';
 s.getRange('E5:L6').format.font.bold=true;s.getRange('E5:L6').format.horizontalAlignment='center';
 s.freezePanes.freezeRows(6);s.freezePanes.freezeColumns(4);
}
model.tabColor='#233D59';inputs.tabColor='#557695';
val(inputs,'C8','Source: original synthetic scenario. No external company data.');
val(inputs,'C10','Historical financial data');section(inputs,10,'Historical financial data');
const histories={11:['Revenue',[100,112,126]],12:['Cost of goods sold',[60,66.08,73.08]],13:['Operating expenses excluding D&A',[22,24.64,27.72]],14:['Depreciation & amortization',[3,3.4,3.8]],15:['Capital expenditures',[4,4.5,5.2]],16:['Accounts receivable',[14,15.8,18]],17:['Inventory',[10,11.2,12.6]],18:['Accounts payable',[8,9,10.1]],19:['Cash taxes on EBIT',[3.75,4.47,5.35]]};
for(const [r,[label,values]] of Object.entries(histories)){val(inputs,'C'+r,label);values.forEach((v,i)=>val(inputs,cols[i]+r,v));inputs.getRange(`E${r}:G${r}`).format.font.color='#0000FF';}
section(inputs,22,'Forecast assumptions');
const drivers={23:['Revenue growth',[.10,.09,.08,.07,.06]],24:['Gross margin',[.42,.425,.43,.435,.44]],25:['Operating expenses / revenue',[.22,.218,.216,.214,.212]],26:['D&A / revenue',[.03,.03,.03,.03,.03]],27:['Capital expenditures / revenue',[.045,.045,.045,.045,.045]],28:['Accounts receivable / revenue',[.145,.147,.148,.148,.148]],29:['Inventory / revenue',[.10,.10,.10,.10,.10]],30:['Accounts payable / revenue',[.08,.08,.08,.08,.08]],31:['Cash tax rate on positive EBIT',[.25,.25,.25,.25,.25]]};
for(const [r,[label,values]] of Object.entries(drivers)){val(inputs,'C'+r,label);values.forEach((v,i)=>val(inputs,cols[i+3]+r,v));inputs.getRange(`H${r}:L${r}`).format.font.color='#0000FF';inputs.getRange(`H${r}:L${r}`).format.fill='#FFF7DC';inputs.getRange(`E${r}:L${r}`).setNumberFormat('0.0%');inputs.getRange(`C${r}:L${r}`).format.font.italic=true;}
section(inputs,34,'Opening balances and conventions');
val(inputs,'C35','2022 closing net working capital');val(inputs,'E35',14);inputs.getRange('E35').format.font.color='#0000FF';
for(const [r,t] of [[37,'Costs, capex and cash taxes are positive amounts and deducted in the model.'],[38,'Net working capital = accounts receivable + inventory − accounts payable.'],[39,'A positive change in net working capital consumes cash.'],[40,'Cash taxes = 25% of positive forecast EBIT. No loss tax benefit or NOL schedule.'],[41,'Unlevered FCF = EBIT − cash taxes + D&A − capex − change in NWC.'],[42,'This is an operating / cash-flow model. Debt, interest and a full balance sheet are excluded.'],[44,'Blue: numerical input. Black: same-sheet formula. Green: cross-sheet formula.']])val(inputs,'C'+r,t);
section(model,8,'Operating results');
const labels={9:'Revenue',10:'Revenue growth',12:'Cost of goods sold',13:'Gross profit',14:'Gross margin',16:'Operating expenses excluding D&A',17:'EBITDA',18:'EBITDA margin',20:'Depreciation & amortization',21:'EBIT',22:'EBIT margin',24:'Cash taxes on EBIT',25:'NOPAT',27:'Net working capital',28:'Accounts receivable',29:'Inventory',30:'Accounts payable',31:'Net working capital',32:'Change in net working capital',34:'Unlevered free cash flow',35:'NOPAT',36:'Add: depreciation & amortization',37:'Less: capital expenditures',38:'Less: change in net working capital',39:'Unlevered free cash flow',40:'FCF / revenue',42:'Cumulative forecast free cash flow'};
for(const [r,label] of Object.entries(labels))val(model,'C'+r,label);
section(model,27,'Net working capital');section(model,34,'Unlevered free cash flow');
for(let i=0;i<8;i++){
 const c=cols[i],p=cols[i-1],h=i<3;
 const set=(r,f)=>formula(model,c+r,f);
 set(9,h?`='Assumptions'!${c}11`:`=${p}9*(1+'Assumptions'!${c}23)`);
 if(i)set(10,`=${c}9/${p}9-1`);else val(model,c+'10','n.a.');
 set(12,h?`='Assumptions'!${c}12`:`=${c}9*(1-'Assumptions'!${c}24)`);
 set(13,`=${c}9-${c}12`);set(14,`=${c}13/${c}9`);
 set(16,h?`='Assumptions'!${c}13`:`=${c}9*'Assumptions'!${c}25`);
 set(17,`=${c}13-${c}16`);set(18,`=${c}17/${c}9`);
 set(20,h?`='Assumptions'!${c}14`:`=${c}9*'Assumptions'!${c}26`);
 set(21,`=${c}17-${c}20`);set(22,`=${c}21/${c}9`);
 set(24,h?`='Assumptions'!${c}19`:`=MAX(${c}21,0)*'Assumptions'!${c}31`);set(25,`=${c}21-${c}24`);
 for(const [r,ir,dr] of [[28,16,28],[29,17,29],[30,18,30]])set(r,h?`='Assumptions'!${c}${ir}`:`=${c}9*'Assumptions'!${c}${dr}`);
 set(31,`=SUM(${c}28:${c}29)-${c}30`);set(32,i?`=${c}31-${p}31`:`=${c}31-'Assumptions'!$E$35`);
 set(35,`=${c}25`);set(36,`=${c}20`);set(37,h?`='Assumptions'!${c}15`:`=${c}9*'Assumptions'!${c}27`);set(38,`=${c}32`);
 set(39,`=SUM(${c}35:${c}36)-SUM(${c}37:${c}38)`);set(40,`=${c}39/${c}9`);
 if(!h)set(42,`=SUM($H39:${c}39)`);
 for(const [r,fr] of [[23,10],[24,14]])if(h&&!(i===0&&r===23))formula(inputs,c+r,`='Operating Model'!${c}${fr}`);
 for(const [r,fr] of [[25,16],[26,20],[27,37],[28,28],[29,29],[30,30]])if(h)formula(inputs,c+r,`='Operating Model'!${c}${fr}/'Operating Model'!${c}9`);
 if(h)formula(inputs,c+'31',`='Operating Model'!${c}24/'Operating Model'!${c}21`);
}
for(const r of [10,14,18,22,40]){model.getRange(`E${r}:L${r}`).setNumberFormat('0.0%');model.getRange(`C${r}:L${r}`).format.font.italic=true;}
for(const r of [9,13,17,21,25,31,39,42])total(model,r,[9,17,25,39,42].includes(r));
section(checks,8,'Arithmetic and assumption checks');
val(checks,'C10','Gross profit reconciliation');val(checks,'C11','EBIT reconciliation');val(checks,'C12','Working capital reconciliation');val(checks,'C13','Cash tax reconciliation');
for(const c of cols){
 for(const [r,f] of [[10,`='Operating Model'!${c}13-('Operating Model'!${c}9-'Operating Model'!${c}12)`],[11,`='Operating Model'!${c}21-('Operating Model'!${c}17-'Operating Model'!${c}20)`],[12,`='Operating Model'!${c}31-('Operating Model'!${c}28+'Operating Model'!${c}29-'Operating Model'!${c}30)`],[13,`='Operating Model'!${c}24-MAX('Operating Model'!${c}21,0)*'Assumptions'!${c}31`]])formula(checks,c+r,f);
}
checks.getRange('E10:L13').setNumberFormat('0.00;(0.00);0.00');checks.getRange('E10:L13').format.font.color='#000000';
checks.getRange('E10:L13').conditionalFormats.addCustom('ABS(E10)>0.000001',{fill:'#FDE9E7',font:{bold:true,color:'#B91C1C'}});
val(checks,'C16','Tolerance: $0.000001m. Zero indicates that the named reconciliation passes.');
val(checks,'C18','These checks cover only the named relationships. They are not a complete model audit.');
// Independent direct calculations: no workbook formulas or reference outputs used.
let priorRev=126,priorNwc=20.5,cumulative=0;
const expected=[];
for(let j=0;j<5;j++){
 const a=r=>drivers[r][1][j],rev=priorRev*(1+a(23)),ebitda=rev*(a(24)-a(25)),da=rev*a(26),ebit=ebitda-da,tax=Math.max(0,ebit)*a(31),nwc=rev*(a(28)+a(29)-a(30)),delta=nwc-priorNwc,capex=rev*a(27),fcf=ebit-tax+da-capex-delta;
 cumulative+=fcf;expected.push({year:2026+j,column:cols[j+3],revenue:rev,ebitda,ebit,tax,nwc,delta,capex,fcf,cumulative});priorRev=rev;priorNwc=nwc;
}
wb.recalculate();
for(const e of expected)for(const [r,key] of [[9,'revenue'],[17,'ebitda'],[21,'ebit'],[24,'tax'],[31,'nwc'],[32,'delta'],[37,'capex'],[39,'fcf'],[42,'cumulative']]){const actual=model.getRange(e.column+r).values[0][0];if(typeof actual!=='number'||Math.abs(actual-e[key])>1e-8)throw Error(`Mismatch ${e.column}${r}: ${actual} vs ${e[key]}`);}
// Verify live input propagation, then restore before exporting.
const baseline=model.getRange('H39').values[0][0];val(inputs,'H28',.155);wb.recalculate();
if(Math.abs(model.getRange('H39').values[0][0]-(baseline-1.386))>1e-8)throw Error('Input propagation failed');
val(inputs,'H28',.145);wb.recalculate();
const inspection=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:30},maxChars:2000});
await fs.writeFile(root+'/references/case-001/formula-scan.txt',inspection.ndjson);
await fs.writeFile(root+'/references/case-001/expected.json',JSON.stringify(expected,null,2));
for(const s of [model,inputs,checks]){const blob=await wb.render({sheetName:s.name,range:s===model?'C2:L44':s===inputs?'C2:L45':'C2:L19',scale:1.5,format:'png'});await fs.writeFile(`${previews}/${s.name}.png`,new Uint8Array(await blob.arrayBuffer()));}
await (await SpreadsheetFile.exportXlsx(wb)).save(root+'/references/case-001/reference.xlsx');
// The single planted root-cause error is the 2027 FCF formula. Styles stay untouched.
formula(model,'I39','=SUM(I35:I36)-I37+I38');wb.recalculate();
const wrong=model.getRange('I39').values[0][0];
if(Math.abs(wrong-expected[1].fcf-2*expected[1].delta)>1e-8)throw Error('Planted error impact mismatch');
await (await SpreadsheetFile.exportXlsx(wb)).save(root+'/cases/case-001/model.xlsx');
await fs.writeFile(root+'/references/case-001/error-manifest.json',JSON.stringify({id:'case-001',root_cell:'Operating Model!I39',original_formula:'=SUM(I35:I36)-SUM(I37:I38)',altered_formula:'=SUM(I35:I36)-I37+I38',correct_fcf:expected[1].fcf,submitted_fcf:wrong,overstatement:2*expected[1].delta,downstream:['Operating Model!I40','Operating Model!I42:L42'],native_excel_verified:false},null,2));
console.log(JSON.stringify({expected,wrong,scan:inspection.ndjson}));
