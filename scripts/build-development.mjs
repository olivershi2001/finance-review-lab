// Optional authoring tool: requires the OpenAI Artifact Tool runtime.
// Evaluation and verification do not require this dependency.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const previews=process.env.FRL_PREVIEW_DIR || path.join(root,'build-previews');
await fs.mkdir(previews,{recursive:true});
const cols=['E','F','G','H','I'];
const fmt='#,##0.0;(#,##0.0);"–"';
const put=(s,c,v)=>s.getRange(c).values=[[v]];
function form(s,c,f){s.getRange(c).formulas=[[f]];s.getRange(c).format.font.color=f.includes('!')?'#008000':'#000000';}
function band(s,r,label){put(s,'C'+r,label);s.getRange(`C${r}:I${r}`).format={fill:'#233D59',font:{bold:true,color:'#FFFFFF'}};}
function total(s,r){s.getRange(`C${r}:I${r}`).format.font.bold=true;s.getRange(`E${r}:I${r}`).format.borders={top:{style:'thin',color:'#9AA8B5'}};}
function note(s,r,text){put(s,'C'+r,text);}
function base(mainName,company){
 const wb=Workbook.create(),m=wb.worksheets.add(mainName),a=wb.worksheets.add('Assumptions');
 for(const s of [m,a]){
  s.showGridLines=false;s.getRange('A1:J40').format.font={name:'Arial',size:10,color:'#000000'};
  s.getRange('A1:B40').format.columnWidth=2;s.getRange('C1:C40').format.columnWidth=40;s.getRange('D1:D40').format.columnWidth=3;
  s.getRange('E1:I40').format.columnWidth=15;s.getRange('A1:J40').format.rowHeight=19;
  s.getRange('E7:I36').setNumberFormat(fmt);s.getRange('E1:I40').format.horizontalAlignment='right';
  s.getRange('C1:I40').format.verticalAlignment='center';
  put(s,'C2',company);s.getRange('C2:I2').format.font={size:14,bold:true};
  put(s,'C3','USD millions, except ratios and per-share values.');s.getRange('C3:I3').format.font.italic=true;
  cols.forEach((c,i)=>{put(s,c+'5',2026+i);put(s,c+'6','Forecast');});
  s.getRange('E5:I6').format={fill:'#E7EDF3',font:{bold:true},horizontalAlignment:'center'};
  s.freezePanes.freezeRows(6);s.freezePanes.freezeColumns(4);
 }
 m.tabColor='#233D59';a.tabColor='#557695';
 note(a,8,'Source: original synthetic scenario. Calendar year-end periods.');
 note(a,36,'Blue: numerical input. Black: same-sheet formula. Green: cross-sheet formula.');
 return {wb,m,a};
}
function input(s,r,label,values,format=fmt){put(s,'C'+r,label);s.getRange(`E${r}:I${r}`).values=[values];s.getRange(`E${r}:I${r}`).format.font.color='#0000FF';s.getRange(`E${r}:I${r}`).format.fill='#FFF7DC';s.getRange(`E${r}:I${r}`).setNumberFormat(format);}
function assertValue(s,c,v){const actual=s.getRange(c).values[0][0];if(typeof actual!=='number'||Math.abs(actual-v)>1e-8)throw Error(`${s.name}!${c}: ${actual} vs ${v}`);}
function task(company,focus){return `# ${company}: model audit\n\nAudit the attached model.xlsx for material formula errors. ${focus} Treat supplied inputs as authoritative and use the conventions on Assumptions. There may be zero, one or multiple errors. Do not replace stated conventions with preferred practices.\n\nFor each genuine root cause, identify the sheet and cell, quote the existing formula, explain the error, provide a corrected live Excel formula, quantify its impact and list affected downstream cells. Group symptoms under their root cause. Leave correct work unchanged.\n\nReturn an audit memo and a JSON object with a findings array. Each finding must contain sheet, cell, existing_formula, diagnosis, corrected_formula, correct_value, original_minus_correct, downstream_cells and explanation. Monetary amounts are USD millions, except an explicitly per-share output. Use at least four decimals for numerical impacts. For no material errors, return {"findings": []} with a short explanation.\n\nOnly this brief and model.xlsx belong in an evaluation session. Do not access reference assets or public answer keys.\n`;}
async function save(id,context,expected,mutate,taskText,perturb){
 const {wb,m,a}=context,dir=path.join(root,'cases',id),ref=path.join(root,'references',id);
 await fs.mkdir(dir,{recursive:true});await fs.mkdir(ref,{recursive:true});
 // Compact empty spacer rows so section checks stay with their schedules in print.
 // Text stays at its authored font size; populated rows retain readable spacing.
 for(const s of [m,a])for(let r=1;r<=40;r++){
  const range=s.getRange(`C${r}:I${r}`),values=range.values.flat(),formulas=range.formulas.flat();
  if(values.every(v=>v==null||v==='')&&formulas.every(v=>v==null||v===''))s.getRange(`A${r}:J${r}`).format.rowHeight=6;
 }
 wb.recalculate();
 for(const [cell,value] of Object.entries(expected))assertValue(m,cell,value);
 const perturbations=await perturb();wb.recalculate();
 for(const [cell,value] of Object.entries(expected))assertValue(m,cell,value);
 const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:50},maxChars:3000});
 if(!scan.ndjson.includes('matched 0'))throw Error('Unexpected formula errors: '+scan.ndjson);
 for(const s of [m,a]){const b=await wb.render({sheetName:s.name,range:'C2:I37',scale:1.5,format:'png'});await fs.writeFile(path.join(previews,`${id}-${s.name}.png`),new Uint8Array(await b.arrayBuffer()));}
 await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(ref,'reference.xlsx'));
 await mutate();wb.recalculate();
 await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(dir,'model.xlsx'));
 await fs.writeFile(path.join(dir,'task.md'),taskText);
 await fs.writeFile(path.join(ref,'expected.json'),JSON.stringify({sheet:m.name,cells:expected},null,2)+'\n');
 await fs.writeFile(path.join(ref,'authoring-validation.json'),JSON.stringify({engine:'OpenAI Artifact Tool',independent_numeric_outputs:Object.keys(expected).length,formula_error_scan:scan.ndjson,perturbations,native_excel_verified:false,visual_review:'pending'},null,2)+'\n');
 console.log(`${id}: exported reference and audit workbook`);
}

// Debt: principal flows are period totals; specified convention is average opening/closing debt.
{
 const ctx=base('Debt Schedule','Birch Logistics'),{wb,m,a}=ctx;
 band(a,10,'Debt and operating assumptions');
 input(a,11,'Opening debt at start of 2026',[180,null,null,null,null]);
 input(a,12,'New borrowing',[20,0,0,0,0]);input(a,13,'Principal repayment',[30,35,40,45,50]);
 input(a,14,'Annual cash interest rate',[.08,.085,.09,.085,.08],'0.0%');input(a,15,'EBITDA',[42,44,46,48,50]);
 note(a,19,'Interest uses arithmetic average opening and closing debt, including all borrowings.');
 note(a,20,'Annual flows use this convention regardless of actual transaction dates.');
 note(a,21,'Borrowings and repayments are positive inputs. There are no fees or PIK interest.');
 note(a,22,'Coverage = EBITDA / cash interest. Debt repayment is not an EBITDA expense.');
 band(m,8,'Debt roll-forward');
 const labels={9:'Opening debt',10:'Add: new borrowing',11:'Less: principal repayment',13:'Closing debt',16:'Interest and coverage',17:'Average debt balance',19:'Annual cash interest rate',20:'Cash interest expense',21:'EBITDA',22:'Interest coverage',24:'Cumulative cash interest',27:'Debt roll-forward reconciliation'};
 for(const [r,l] of Object.entries(labels))put(m,'C'+r,l);band(m,16,'Interest and coverage');
 let opening=180,cumulative=0;const expected={};
 cols.forEach((c,i)=>{const p=cols[i-1],borrow=[20,0,0,0,0][i],repay=[30,35,40,45,50][i],rate=[.08,.085,.09,.085,.08][i],closing=opening+borrow-repay,average=(opening+closing)/2,interest=average*rate;cumulative+=interest;
  form(m,c+'9',i?`=${p}13`:`='Assumptions'!${c}11`);form(m,c+'10',`='Assumptions'!${c}12`);form(m,c+'11',`='Assumptions'!${c}13`);
  form(m,c+'13',`=SUM(${c}9:${c}10)-${c}11`);form(m,c+'17',`=SUM(${c}9,${c}13)/2`);form(m,c+'19',`='Assumptions'!${c}14`);
  form(m,c+'20',`=${c}17*${c}19`);form(m,c+'21',`='Assumptions'!${c}15`);form(m,c+'22',`=IF(${c}20=0,"n.a.",${c}21/${c}20)`);form(m,c+'24',`=SUM($E20:${c}20)`);
  form(m,c+'27',`=${c}13-(${c}9+${c}10-${c}11)`);
  Object.assign(expected,{[c+'9']:opening,[c+'13']:closing,[c+'17']:average,[c+'20']:interest,[c+'22']:[42,44,46,48,50][i]/interest,[c+'24']:cumulative,[c+'27']:0});opening=closing;
 });
 m.getRange('E19:I19').setNumberFormat('0.0%');m.getRange('C19:I19').format.font.italic=true;m.getRange('E22:I22').setNumberFormat('0.0"x"');m.getRange('C22:I22').format.font.italic=true;
 for(const r of [13,20,24])total(m,r);m.getRange('E27:I27').setNumberFormat('0.00;(0.00);0.00');
 m.getRange('E27:I27').conditionalFormats.addCustom('ABS(E27)>0.000001',{fill:'#FDE9E7',font:{color:'#B91C1C',bold:true}});
 note(m,30,'Reconciliation checks principal flows only. It is not a full audit of interest calculations.');
 await save('dev-002',ctx,expected,async()=>form(m,'G20','=G9*G19'),task('Birch Logistics','Review the debt schedule and cash interest calculations.'),async()=>{
  const tests=[];put(a,'G14',0);wb.recalculate();assertValue(m,'G20',0);tests.push('Zero rate: zero interest and n.a. coverage');if(m.getRange('G22').values[0][0]!=='n.a.')throw Error('zero-rate guard');
  put(a,'G14',.09);put(a,'G13',20);wb.recalculate();assertValue(m,'G20',(135+115)/2*.09);tests.push('Lower principal repayment raises average debt interest');put(a,'G13',40);return tests;
 });
}
// Valuation: yearly LTM marks, consolidated EBITDA and explicit senior claims.
{
 const ctx=base('Valuation','Juniper Services'),{wb,m,a}=ctx;
 band(a,10,'Valuation assumptions');
 input(a,11,'LTM consolidated EBITDA',[48,52,57,61,66]);input(a,12,'Enterprise value / LTM EBITDA',[8,8.25,8.5,8.5,8.75],'0.0"x"');
 input(a,13,'Debt principal',[150,140,125,110,95]);input(a,14,'Preferred equity claim',[20,20,20,20,20]);input(a,15,'Noncontrolling interest value',[15,16,17,18,19]);input(a,16,'Excess cash',[25,30,38,45,52]);input(a,17,'Nonoperating investment value',[8,8,9,9,10]);input(a,18,'Diluted shares (millions)',[40,41,42,43,44]);
 note(a,21,'Each column is a hypothetical year-end valuation using that calendar year\'s LTM EBITDA.');
 note(a,22,'Consolidated EBITDA includes noncontrolling interests; subtract their stated equity value.');
 note(a,23,'Enterprise value excludes excess cash and the nonoperating investment. Add both to equity.');
 note(a,24,'Debt, preferred and noncontrolling claims are deducted. All claims are stated values.');
 note(a,25,'Share counts are millions. Equity value in USD millions / shares in millions = USD per share.');
 band(m,8,'Enterprise value');
 for(const [r,l] of Object.entries({9:'LTM consolidated EBITDA',10:'Enterprise value / LTM EBITDA',11:'Enterprise value',14:'Less: debt principal',15:'Less: preferred equity claim',16:'Less: noncontrolling interest',17:'Add: excess cash',18:'Add: nonoperating investment',21:'Common equity value',23:'Diluted shares (millions)',24:'Common equity value per share',28:'Share count positive (1 = yes)'}))put(m,'C'+r,l);
 band(m,13,'Enterprise to common equity');const expected={};
 cols.forEach((c,i)=>{
  for(const [r,ir] of [[9,11],[10,12],[14,13],[15,14],[16,15],[17,16],[18,17],[23,18]])form(m,c+r,`='Assumptions'!${c}${ir}`);
  form(m,c+'11',`=${c}9*${c}10`);form(m,c+'21',`=${c}11-SUM(${c}14:${c}16)+SUM(${c}17:${c}18)`);form(m,c+'24',`=IF(${c}23=0,"n.a.",${c}21/${c}23)`);form(m,c+'28',`=IF(${c}23>0,1,0)`);
  const ev=[48,52,57,61,66][i]*[8,8.25,8.5,8.5,8.75][i],equity=ev-[150,140,125,110,95][i]-20-[15,16,17,18,19][i]+[25,30,38,45,52][i]+[8,8,9,9,10][i];Object.assign(expected,{[c+'11']:ev,[c+'21']:equity,[c+'24']:equity/[40,41,42,43,44][i]});
 });
 for(const r of [11,21,24])total(m,r);m.getRange('E24:I24').setNumberFormat('$0.00;($0.00);"–"');m.getRange('E10:I10').setNumberFormat('0.0"x"');m.getRange('C10:I10').format.font.italic=true;
 note(m,31,'Share-count check covers only denominator validity. It is not a full valuation audit.');
 await save('dev-003',ctx,expected,async()=>form(m,'G21','=G11-SUM(G14:G16)-G17+G18'),task('Juniper Services','Review the valuation bridge and diluted per-share calculations.'),async()=>{
  put(a,'G16',0);wb.recalculate();assertValue(m,'G21',331.5);put(a,'G16',38);
  put(a,'G18',0);wb.recalculate();if(m.getRange('G24').values[0][0]!=='n.a.')throw Error('zero shares guard');put(a,'G18',42);
  return ['Zero cash: equity bridge responds correctly','Zero shares: per-share result unavailable rather than zero'];
 });
}
// Control: revenue contraction releases working capital, temporary capex depresses FCF.
{
 const ctx=base('Operating Model','Maple Equipment'),{wb,m,a}=ctx;
 band(a,10,'Forecast assumptions');input(a,11,'Opening 2025 revenue',[90,null,null,null,null]);input(a,12,'Revenue growth',[.08,-.12,.06,.07,.05],'0.0%');input(a,13,'EBITDA margin',[.19,.17,.18,.19,.20],'0.0%');input(a,14,'D&A / revenue',[.035,.035,.035,.035,.035],'0.0%');input(a,15,'Capital expenditures / revenue',[.05,.25,.05,.05,.05],'0.0%');input(a,16,'Net working capital / revenue',[.18,.18,.18,.18,.18],'0.0%');input(a,17,'Cash tax rate',[.25,.25,.25,.25,.25],'0.0%');input(a,18,'Opening 2025 net working capital',[16.2,null,null,null,null]);
 note(a,21,'Positive changes in net working capital consume cash; decreases release cash.');note(a,22,'Capex is a positive cash outflow. D&A is a noncash expense added back after tax.');note(a,23,'Taxes apply only to positive EBIT. There is no NOL carry-forward or interest schedule.');note(a,24,'A 2027 facility expansion causes the temporary 25% capex / revenue assumption.');note(a,25,'Forecast assumptions are authoritative. A negative FCF year is permissible.');
 band(m,8,'Operating results');
 for(const [r,l] of Object.entries({9:'Revenue',10:'Revenue growth',12:'EBITDA',13:'EBITDA margin',15:'Depreciation & amortization',16:'EBIT',17:'Cash taxes on positive EBIT',18:'NOPAT',21:'Net working capital',22:'Change in net working capital',25:'NOPAT',26:'Add: depreciation & amortization',27:'Less: capital expenditures',28:'Less: change in net working capital',30:'Unlevered free cash flow',31:'FCF / revenue',33:'Cumulative forecast free cash flow'}))put(m,'C'+r,l);
 band(m,20,'Working capital');band(m,24,'Unlevered free cash flow');
 let rev=90,nwc=16.2,cum=0;const expected={};
 cols.forEach((c,i)=>{const p=cols[i-1];form(m,c+'10',`='Assumptions'!${c}12`);form(m,c+'9',i?`=${p}9*(1+${c}10)`:`='Assumptions'!${c}11*(1+${c}10)`);form(m,c+'13',`='Assumptions'!${c}13`);form(m,c+'12',`=${c}9*${c}13`);form(m,c+'15',`=${c}9*'Assumptions'!${c}14`);form(m,c+'16',`=${c}12-${c}15`);form(m,c+'17',`=MAX(${c}16,0)*'Assumptions'!${c}17`);form(m,c+'18',`=${c}16-${c}17`);form(m,c+'21',`=${c}9*'Assumptions'!${c}16`);form(m,c+'22',i?`=${c}21-${p}21`:`=${c}21-'Assumptions'!${c}18`);form(m,c+'25',`=${c}18`);form(m,c+'26',`=${c}15`);form(m,c+'27',`=${c}9*'Assumptions'!${c}15`);form(m,c+'28',`=${c}22`);form(m,c+'30',`=SUM(${c}25:${c}26)-SUM(${c}27:${c}28)`);form(m,c+'31',`=${c}30/${c}9`);form(m,c+'33',`=SUM($E30:${c}30)`);
  rev*=1+[.08,-.12,.06,.07,.05][i];const eb=rev*[.19,.17,.18,.19,.20][i],da=rev*.035,ebit=eb-da,tax=Math.max(ebit,0)*.25,nextNwc=rev*.18,change=nextNwc-nwc,capex=rev*[.05,.25,.05,.05,.05][i],fcf=ebit-tax+da-capex-change;cum+=fcf;
  Object.assign(expected,{[c+'9']:rev,[c+'12']:eb,[c+'15']:da,[c+'16']:ebit,[c+'17']:tax,[c+'21']:nextNwc,[c+'22']:change,[c+'27']:capex,[c+'30']:fcf,[c+'33']:cum});nwc=nextNwc;
 });
 for(const r of [10,13,31]){m.getRange(`E${r}:I${r}`).setNumberFormat('0.0%');m.getRange(`C${r}:I${r}`).format.font.italic=true;}for(const r of [9,12,16,18,30,33])total(m,r);
 await save('dev-004',ctx,expected,async()=>{},task('Maple Equipment','Review the operating forecast and unlevered cash-flow calculations.'),async()=>{
  const current=m.getRange('F30').values[0][0];put(a,'F15',.05);wb.recalculate();assertValue(m,'F30',current+m.getRange('F9').values[0][0]*.20);put(a,'F15',.25);
  put(a,'H13',.01);wb.recalculate();assertValue(m,'H17',0);put(a,'H13',.19);
  return ['Lower expansion capex increases FCF by the cash savings','Negative EBIT receives no tax benefit'];
 });
}
