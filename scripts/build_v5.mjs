import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const before=await read('data/v4/questions.json');
const after=structuredClone(before);
const reasons=await read('scripts/v5_context_reasons.json');
const meanings=before.filter(q=>q.question_type==='meaning');
const strip=d=>d.replace(/のこと$/,'');
const originalDefs=Object.fromEntries(meanings.map(q=>[q.target_word,q.correct_answer]));
const definitions=Object.fromEntries(meanings.map(q=>[q.target_word,
  q.correct_answer.endsWith('こと')?q.correct_answer:
  q.correct_answer.endsWith('様子')?q.correct_answer.slice(0,-2)+'こと':q.correct_answer+'のこと']));
const wordForDefinition=new Map(Object.entries(originalDefs).map(([w,d])=>[strip(d),w]));
const extraOld='水滴が落ちてこない霧そのもの';
const extraDef='水滴が落ちてこない霧のこと';
const getWord=d=>d===extraOld?'霧':wordForDefinition.get(strip(d));
const definitionFor=w=>w==='霧'?extraDef:definitions[w];
const byId=Object.fromEntries(after.map(q=>[q.id,q]));
byId['JVQ-075-02-C'].prompt='次の場面を表す言葉として、最も適切なものを一つ選びなさい。\n学校は授業用のタブレットを、一年間だけという約束で生徒に渡した';
byId['JVQ-048-04-C'].choices=['結果','帰結','契機'];
// Remove the question sentence, not an arbitrary character range. Preserve nested quotations.
export function scene(q){
  let text=q.prompt.slice(q.prompt.indexOf('\n')+1);
  if(['JVQ-040-04-C','JVQ-048-01-C','JVQ-048-02-C','JVQ-048-04-C','JVQ-112-02-C'].includes(q.id)){
    text=text.slice(0,text.indexOf('。')+1);
  }
  return text.replace(/。$/,'');
}
const missingNames=[];
for(const q of after){
  if(q.question_type==='meaning'){
    const old=before.find(x=>x.id===q.id);
    const words=old.choices.map(getWord);
    if(words.some(w=>!w))throw Error('Unknown definition: '+q.id);
    if(words.some(w=>w!=='霧'&&!old.explanation.includes('「'+w+'」')))missingNames.push(q.id);
    q.choices=words.map(definitionFor);
    q.correct_answer=q.choices[q.correct_index];
    const wrong=words.filter((_,i)=>i!==q.correct_index);
    q.explanation=`「${q.target_word}」は${definitions[q.target_word]}。一方、「${wrong[0]}」は${definitionFor(wrong[0])}。また、「${wrong[1]}」は${definitionFor(wrong[1])}。それぞれの意味の中心を比べて区別しよう。`;
  }else if(q.question_type==='context'){
    const wrong=q.choices.filter((_,i)=>i!==q.correct_index);
    for(const w of q.choices)if(!definitions[w])throw Error('Unknown word: '+w);
    if(!reasons[q.id])throw Error('Missing individual reason: '+q.id);
    q.explanation=`場面「${scene(q)}」は「${q.correct_answer}」に当たる。この場面を「${q.correct_answer}」と判断できるのは、${reasons[q.id]}「${q.correct_answer}」は${definitions[q.correct_answer]}。「${wrong[0]}」は${definitions[wrong[0]]}、「${wrong[1]}」は${definitions[wrong[1]]}であり、この場面の内容とは合わない。`;
  }
}
byId['JLR-005-01'].choices[2]='この数字を見て人気だと話した人がいたかどうか';
byId['JLR-005-01'].explanation='根拠：「十人増えた」だけでは前年の人数が不明で、増加率を求められない。誤答1：前年より十人増えたこと自体は分かる。誤答3：第2文に「活動が大人気になった」と話す人がいたと書かれており、分からないことではない。';
byId['JLR-005-03'].choices[0]='同じ十人増でも割合が違うことを示すこと';
byId['JLR-005-03'].correct_answer=byId['JLR-005-03'].choices[0];
byId['JLR-005-04'].choices[2]='参加者の増加だけで活動の成果を評価する';
byId['JLR-010-03'].explanation=byId['JLR-010-03'].explanation.replace('出欠一覧の作成に限定していない','出欠一覧は、身についた知識の調査とは別のものである');
// Literal rechecking found three abbreviated quotations in the supplied base.
byId['JLR-008-02'].explanation=byId['JLR-008-02'].explanation.replace('調査の時期が古い資料では…','調査の時期が古い資料では、現在の制度を説明できない場合がある');
byId['JLR-008-03'].explanation=byId['JLR-008-03'].explanation.replace('出典と更新時期を確認し…複数の資料を比べるべきだ','出典と更新時期を確認し、必要に応じて複数の資料を比べるべきだ');
byId['JLR-010-02'].explanation=byId['JLR-010-02'].explanation.replace('参加者が多いことと…知識が十分に共有されることは同じではない','参加者が多いことと、必要な知識が十分に共有されることは同じではない');
const csvCell=x=>'"'+String(x??'').replaceAll('"','""')+'"';
const csv=(headers,rows)=>[headers,...rows].map(r=>r.map(csvCell).join(',')).join('\r\n')+'\r\n';
const fields=[...new Set(after.flatMap(Object.keys))];
const columns=fields.filter(k=>!['choices','correct_index'].includes(k));
columns.splice(columns.indexOf('correct_answer'),0,'choice_1','choice_2','choice_3','correct_option');
columns.push('present_fields'); // Preserve absent fields separately from present empty strings.
const row=q=>columns.map(k=>k==='present_fields'?Object.keys(q).join(';'):k==='correct_option'?q.correct_index+1:/^choice_[123]$/.test(k)?q.choices[Number(k.at(-1))-1]:q[k]??'');
const changes=[];
for(let i=0;i<before.length;i++)for(const k of fields){
  if(JSON.stringify(before[i][k])===JSON.stringify(after[i][k]))continue;
  const q=after[i];
  let reason=q.question_type==='context'?'場面ごとの個別根拠・全文引用・正答と誤答語の現行定義を連動更新':q.question_type==='meaning'?'定義を語ごとに固定し、選択肢の語尾をこと型へ統一、誤答語名を明示':'Claude第4回監査本文の個別完成修正を反映';
  if(q.id==='JVQ-075-02-C')reason+='／貸与の期間約束を示し返却行為との重なりを除去';
  if(['JLR-008-02','JLR-008-03','JLR-010-02'].includes(q.id))reason='今回の逐語検証で見つかった省略記号を本文の実際の語句へ展開';
  if(q.id==='JVQ-048-04-C')reason+='／誤答の要因を帰結へ変更し問いの文を引用から除外';
  if(q.id==='JVQ-112-02-C')reason+='／内側のかぎ括弧で途切れた引用を発言への応答まで修復';
  changes.push([q.id,k,JSON.stringify(before[i][k]),JSON.stringify(q[k]),reason]);
}
await fs.mkdir(path.join(root,'data/v5'),{recursive:true});
await fs.writeFile(path.join(root,'data/v5/questions.json'),JSON.stringify(after,null,2)+'\n');
await fs.writeFile(path.join(root,'data/v5/questions.csv'),csv(columns,after.map(row)));
await fs.writeFile(path.join(root,'data/v5/change_map_v4_v5.csv'),csv(['id','field','before','after','reason'],changes));
console.log(JSON.stringify({questions:after.length,changes:changes.length,changedQuestions:new Set(changes.map(r=>r[0])).size,missingNameCount:missingNames.length,missingNames,canonicalDefinitionChanges:meanings.filter(q=>definitions[q.target_word]!==q.correct_answer).length},null,2));
