import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const text=async p=>fs.readFile(path.join(root,p),'utf8');
// Independent CSV parser: handles commas, escaped quotes and embedded line breaks.
function parseCSV(s){
  const rows=[];let row=[],field='',quoted=false;
  for(let i=0;i<s.length;i++){
    const c=s[i];
    if(quoted){if(c==='"'&&s[i+1]==='"'){field+='"';i++;}else if(c==='"')quoted=false;else field+=c;}
    else if(c==='"')quoted=true;
    else if(c===','){row.push(field);field='';}
    else if(c==='\n'||c==='\r'){if(c==='\r'&&s[i+1]==='\n')i++;row.push(field);rows.push(row);row=[];field='';}
    else field+=c;
  }
  assert.equal(quoted,false);
  if(field||row.length){row.push(field);rows.push(row);}
  const header=rows.shift();
  return rows.map(r=>{assert.equal(r.length,header.length);return Object.fromEntries(header.map((k,i)=>[k,r[i]]));});
}
const old=JSON.parse(await text('data/v5/questions.json'));
const data=JSON.parse(await text('data/v6/questions.json'));
const csv=parseCSV(await text('data/v6/questions.csv'));
const change=parseCSV(await text('data/v6/change_map_v5_v6.csv'));
const definitionChangeText=await text('data/v6/definition_changes.csv');
const changedIdText=await text('data/v6/changed_ids.csv');
const awaitReplacementText=await text('data/v6/distractor_replacements.csv');
const checks=[];
function check(name,fn){fn();checks.push({name,status:'PASS'});}
check('1040 questions; ID order and uniqueness',()=>{assert.equal(data.length,1040);assert.equal(new Set(data.map(q=>q.id)).size,1040);assert.deepEqual(data.map(q=>q.id),old.map(q=>q.id));});
check('JSON/CSV independent full-field reverse round trip',()=>{
  assert.equal(csv.length,data.length);
  const back=csv.map(r=>Object.fromEntries(r.present_fields.split(';').map(k=>[k,k==='choices'?[r.choice_1,r.choice_2,r.choice_3]:k==='correct_index'?Number(r.correct_option)-1:k==='grade'?Number(r[k]):r[k]])));
  assert.deepEqual(back,data);
});
check('3 distinct choices; correct index and answer',()=>{for(const q of data){assert.equal(q.choices.length,3);assert.equal(new Set(q.choices).size,3);assert(Number.isInteger(q.correct_index)&&q.correct_index>=0&&q.correct_index<3);assert.equal(q.choices[q.correct_index],q.correct_answer);}});
const m=data.filter(q=>q.question_type==='meaning');
const c=data.filter(q=>q.question_type==='context');
const l=data.filter(q=>q.question_type==='logical_reading');
const defs=Object.fromEntries(m.map(q=>[q.target_word,q.correct_answer]));
const wordByDef=Object.fromEntries(m.map(q=>[q.correct_answer,q.target_word]));
const extras={'細かな水滴が空気中に浮かんで、視界が白くかすむこと':'霧'};
check('500 M / 500 C / 40 reading; 500 unique headwords',()=>{assert.equal(m.length,500);assert.equal(c.length,500);assert.equal(l.length,40);assert.equal(Object.keys(defs).length,500);assert.equal(Object.keys(wordByDef).length,500);});
check('M definitions and named distractors all present in current wording',()=>{
  for(const q of m)for(const d of q.choices){assert(q.explanation.includes(d),q.id+' definition');assert(q.explanation.includes('「'+(wordByDef[d]||extras[d])+'」'),q.id+' word');}
});
check('C all 3 current definitions and word names present; M/C headwords aligned',()=>{
  for(const q of c){assert.equal(q.correct_answer,q.target_word);assert.equal(q.lexeme_id,m.find(x=>x.target_word===q.target_word).lexeme_id);for(const w of q.choices){assert(defs[w],q.id+' unknown');assert(q.explanation.includes('「'+w+'」は'+defs[w]),q.id+' definition');}}
});
// Independent scene derivation: the final sentence ending in a question is not a situation.
function expectedScene(q){
  let s=q.prompt.split('\n').slice(1).join('\n');
  if(/何(?:に当たるか|か)。$/.test(s)){const parts=s.split('。');parts.pop();parts.pop();s=parts.join('。');}
  return s.replace(/。$/,'');
}
check('500 C complete situation quotes, excluding question sentences; nested quotes preserved',()=>{
  for(const q of c){const expected=expectedScene(q);assert(q.prompt.includes(expected));assert(q.explanation.startsWith('場面「'+expected+'」は'),q.id+' quote: '+expected);assert(!expected.endsWith('何に'));}
});
const reasons=JSON.parse(await text('scripts/v5_context_reasons.json'));
check('500 individual reason entries, each used once for its ID',()=>{assert.equal(Object.keys(reasons).length,500);assert.equal(new Set(Object.values(reasons)).size,500);for(const q of c)assert(q.explanation.includes(reasons[q.id]),q.id);});
check('M three choice ending classes are all こと; answer-only ending outliers 0',()=>{for(const q of m)assert(q.choices.every(d=>d.endsWith('こと')),q.id);});
check('Same definition has only one canonical surface across M choices and M/C explanations',()=>{
  const replacementRows=parseCSV(awaitReplacementText);
  const oldWords=Object.fromEntries(old.filter(q=>q.question_type==='meaning').map(q=>[q.correct_answer,q.target_word]));
  oldWords['水滴が落ちてこない霧のこと']='霧';
  const replacements=new Map(replacementRows.map(r=>[r.id+'|'+(Number(r.choice_number)-1),r]));
  let count=0;
  for(const q of m)for(let i=0;i<3;i++){
    const original=old.find(x=>x.id===q.id).choices[i];
    const prev=oldWords[original], edit=replacements.get(q.id+'|'+i), w=edit?.after_word||prev;
    if(edit){assert.equal(edit.before_word,prev);assert.notEqual(i,q.correct_index);assert(edit.selection_reason);count++;}
    assert.equal(q.choices[i],w==='霧'?'細かな水滴が空気中に浮かんで、視界が白くかすむこと':defs[w],q.id);
  }
  assert.equal(count,replacementRows.length);
  assert.equal(data.filter(q=>q.explanation.includes('様子のこと')).length,0);
});
let quoteCount=0;
check('Reading all quoted strings occur verbatim in passage',()=>{
  for(const q of l){const stack=[];for(let i=0;i<q.explanation.length;i++){const ch=q.explanation[i];if(ch==='「')stack.push(i);else if(ch==='」'){assert(stack.length,q.id);const start=stack.pop();const quote=q.explanation.slice(start+1,i);quoteCount++;assert(q.passage.includes(quote),q.id+' absent quote: '+quote);}}assert.equal(stack.length,0);assert(q.prompt.includes(q.passage));}
});
check('Individual requested text edits',()=>{
  const q=Object.fromEntries(data.map(q=>[q.id,q]));
  assert.deepEqual(q['JLR-005-01'].choices,['今年の参加者が去年より増えたという事実','去年の参加者の人数','「大人気になった」と話した人の数']);
  assert(q['JLR-005-01'].prompt.endsWith('「十人増えた」という数字の印象を判断するために、本文が確認したいとしているものは何か。'));
  assert.equal(q['JLR-005-01'].explanation,'根拠：最終文「もとの人数も確認したい」。誤答1：増えたことはすでに本文にある。誤答3：話した人がいたことは書かれているが、その人数は本文が確認したいとしているものではない。');
  assert.equal(defs['当面'],'さしあたり、しばらくの間であること');
  assert.equal(defs['緊張'],'不安や重要な場面を前にして、心身がこわばること');
  assert.equal(defs['息をのむ'],'驚きや緊張で、一瞬息が止まること');
  assert(q['JVQ-084-03-M'].choices.includes('細かな水滴が空気中に浮かんで、視界が白くかすむこと'));
  assert(!defs['霧']);
  assert(q['JVQ-075-02-C'].prompt.endsWith('学校は授業用のタブレットを、一年間だけという約束で生徒に渡した'));
  assert.deepEqual(q['JVQ-048-04-C'].choices,['結果','帰結','契機']);
  assert(q['JVQ-112-02-C'].explanation.includes('答えた」は'));
  assert.equal(q['JLR-005-03'].choices[0],'同じ十人増でも割合が違うことを示すこと');
  assert.equal(q['JLR-005-04'].choices[2],'参加者の増加だけで活動の成果を評価する');
  assert(q['JLR-010-03'].explanation.includes('出欠一覧は、身についた知識の調査とは別のものである'));
});
const diff=[];
for(let i=0;i<old.length;i++)for(const k of new Set([...Object.keys(old[i]),...Object.keys(data[i])])){
  if(JSON.stringify(old[i][k])!==JSON.stringify(data[i][k]))diff.push([data[i].id,k,JSON.stringify(old[i][k]),JSON.stringify(data[i][k])]);
}
check('Change map matches recomputed JSON differences: IDs, fields, before and after, no extras',()=>{
  assert.equal(new Set(change.map(r=>r.id+'|'+r.field)).size,change.length);
  const sort=a=>a.sort((x,y)=>JSON.stringify(x).localeCompare(JSON.stringify(y)));
  assert.deepEqual(sort(change.map(r=>[r.id,r.field,r.before,r.after])),sort(diff));
  assert(change.every(r=>r.reason.length>0));
});
check('Grade, furigana policy, reading passages, IDs and order unchanged',()=>{
  for(let i=0;i<data.length;i++)for(const k of ['grade','grade_policy','furigana_policy','passage','id'])assert.deepEqual(data[i][k],old[i][k]);
});
const changedIds=new Set(diff.map(x=>x[0]));
const countType=type=>data.filter(q=>q.question_type===type&&changedIds.has(q.id)).length;
const literalMixed=m.filter(q=>q.choices.some(d=>d.endsWith('のこと'))&&!q.choices.every(d=>d.endsWith('のこと'))).map(q=>q.id);
check('Literal のこと mixed questions zero; のこと ending choices zero',()=>{assert.equal(literalMixed.length,0);assert.equal(m.flatMap(q=>q.choices).filter(d=>d.endsWith('のこと')).length,0);});
const outliers=(items,suffix)=>items.filter(q=>q.choices.every((d,i)=>i===q.correct_index||d.endsWith(suffix)!==q.correct_answer.endsWith(suffix))).map(q=>q.id);
const beforeOutliers=outliers(old.filter(q=>q.question_type==='meaning'),'のこと');
const afterOutliers=outliers(m,'であること');
check('Answer-only ending type outliers zero (であること / other こと)',()=>{assert.equal(beforeOutliers.length,45);assert.deepEqual(afterOutliers,[]);});
check('Definition conversion 97 source headwords and exact linked wording',()=>{
  const changes=parseCSV(definitionChangeText);
  assert.equal(old.filter(q=>q.question_type==='meaning'&&q.correct_answer.endsWith('のこと')).length,97);
  for(const row of changes){assert.equal(row.after,row.word==='霧'?'細かな水滴が空気中に浮かんで、視界が白くかすむこと':defs[row.word]);}
});
check('Changed ID file matches recomputed differences',()=>{assert.deepEqual(parseCSV(changedIdText).map(r=>[r.id,r.question_type,r.changed_fields]),data.flatMap((q,i)=>{const fields=Object.keys(q).filter(k=>JSON.stringify(q[k])!==JSON.stringify(old[i][k]));return fields.length?[[q.id,q.question_type,fields.join(';')]]:[]}));});
const hashes={};
for(const p of ['data/v5/questions.json','data/v6/questions.json','data/v6/questions.csv','data/v6/change_map_v5_v6.csv'])hashes[p]=crypto.createHash('sha256').update(await fs.readFile(path.join(root,p))).digest('hex');
const result={base_commit:'4b525c907d28ca3909f6b3b05cafcd3841b8b2c0',overall_status:checks.some(c=>c.status==='UNMET')?'DRAFT_WITH_UNMET_REQUIREMENT':'MECHANICAL_CHECKS_PASSED',questions:data.length,checks,changes:diff.length,changed_questions:changedIds.size,changed_by_type:{meaning:countType('meaning'),context:countType('context'),logical_reading:countType('logical_reading')},reading_quotes:quoteCount,answer_only_type_outlier_ids:afterOutliers,base_outlier_ids:beforeOutliers,distractor_replacements:parseCSV(awaitReplacementText).length,literal_no_koto_mixed_count:literalMixed.length,literal_no_koto_mixed_ids:literalMixed,hashes};
await fs.mkdir(path.join(root,'reports'),{recursive:true});
await fs.writeFile(path.join(root,'reports/v6_verification_results.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
