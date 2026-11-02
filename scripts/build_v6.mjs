import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const before=await read('data/v5/questions.json'), after=structuredClone(before);
const meanings=before.filter(q=>q.question_type==='meaning');
const originalDefs=Object.fromEntries(meanings.map(q=>[q.target_word,q.correct_answer]));
const oldWords=Object.fromEntries(meanings.map(q=>[q.correct_answer,q.target_word]));
oldWords['水滴が落ちてこない霧のこと']='霧';
const definitions=Object.fromEntries(Object.entries(originalDefs).map(([w,d])=>[w,d.replace(/のこと$/,'であること')]));
Object.assign(definitions,{
 '当面':'さしあたり、しばらくの間であること',
 '緊張':'不安や重要な場面を前にして、心身がこわばること',
 '息をのむ':'驚きや緊張で、一瞬息が止まること',
 '四面楚歌':'周囲がすべて敵や反対者で、助けがない状況に置かれていること',
 '千載一遇':'めったにない絶好の機会に巡り合うこと',
 '霧':'細かな水滴が空気中に浮かんで、視界が白くかすむこと'
});
// One manually selected distractor per outlier; no automatic nearest-word selection.
// Each pair is [old distractor, replacement, semantic distinction used in selection].
const replacements={
 '105-01':['試行錯誤','直前','ごく短い期間と、ある時点のすぐ前を区別。元からある「であること」定義も全件再検査'],
 '108-01':['前途多難','暫定的','逃れる方法のない状態と、正式決定までの仮の状態を区別。四面楚歌の定義更新に伴う型の再調整'],
 '003-03':['証拠','確認','未来の出来事を考える行為と、間違いを確かめる行為を区別。推測は採用しない'],
 '011-01':['期待','落胆','心配がなくなって安心することと、期待外れで失望することを区別'],
 '011-03':['落胆','不安','よい結果を待つ気持ちと、先行きを心配する気持ちを区別'],
 '012-01':['満足','不満','強い喜びと、満足できない気持ちを区別'],
 '013-02':['いら立ち','期待','現状への不満足と、よい結果を待つ気持ちを区別'],
 '015-04':['謙虚','偏見','卑しいやり方と、根拠のない決めつけの見方を区別'],
 '017-03':['無関心','不安','知りたい気持ちと、先行きを心配する気持ちを区別'],
 '019-04':['寛容','好奇心','根拠のない決めつけと、未知を知りたい気持ちを区別'],
 '033-01':['説明文','校正','様子を表す行為と、文字や表記の誤りを直す行為を区別'],
 '038-01':['同音異義語','引用','一語に複数の意味があることと、他の文章の言葉を用いる行為を区別'],
 '039-02':['並列','因果','予想に反する接続と、原因・結果の関係を区別'],
 '039-04':['因果','並列','別の表現で言い直す行為と、同じ位置づけの内容を並べる行為を区別'],
 '040-04':['読破','論拠','情報源となる本・資料と、主張を支える根拠を区別'],
 '042-01':['検証','傾向','調査前の仮の説明と、全体に見られる方向を区別'],
 '043-02':['偏り','原因','決まりに当てはまらないものと、結果を引き起こす事柄を区別'],
 '043-04':['傾向','中立','値などがそろわないことと、立場が偏らないことを区別'],
 '044-02':['偏向','傾向','自分の感じ方を中心とする見方と、全体に見られる方向を区別'],
 '047-04':['断言','主観','真偽を疑う気持ちと、自分の感じ方を中心とする見方を区別'],
 '052-02':['特権','選挙','しなければならないことと、投票で代表者を選ぶ行為を区別'],
 '053-01':['立法','選挙','政策を実行する働きと、投票で代表者を選ぶ行為を区別'],
 '053-03':['選挙','司法','法律をつくる働きと、法律に基づき争いを裁く働きを区別'],
 '055-01':['供給','権利','商品を買おうとする求めと、正当に主張できる資格・利益を区別'],
 '058-04':['平等','法律','規則に従って整った状態と、議会などが定める規則を区別'],
 '059-02':['国際','地域','領土・住民と政治的まとまりを持つ社会と、一定範囲の場所・社会を区別'],
 '059-04':['地域','国際','地球全体に及ぶことと、国と国の間に関わることを区別'],
 '060-03':['事件','生産','自然現象などによる大きな被害と、価値あるものをつくる行為を区別'],
 '061-02':['恒久','直前','時点の直後と直前を区別'],
 '061-04':['直後','維持','長く変わらず続くことと、現在の状態を保つ行為を区別'],
 '063-01':['再開','直前','出来事の最初のきっかけと、ある時点のすぐ前を区別'],
 '081-03':['日差し','夕映え','見る向こうから光が当たることと、夕日で赤く照らされることを区別'],
 '082-03':['ささやき','日差し','大きな音と、太陽から差し込む光を区別'],
 '085-02':['夕映え','快晴','曇った天気と、雲がほとんどない天気を区別'],
 '085-04':['快晴','夕映え','朝になり始めることと、夕日で赤く照らされることを区別'],
 '090-02':['硬質','粗い','表面がすべすべしていることと、きめ細かくないことを区別'],
 '090-04':['粗い','硬質','曲げたり考えを変えたりできる性質と、硬くしっかりした性質を区別'],
 '091-03':['無表情','期待','沈んだ気持ちと、よい結果を待つ気持ちを区別'],
 '095-01':['落葉','薄明','若葉の緑と、日の出前・日没後の明るさを区別'],
 '111-01':['誇大','意図','事実と違う内容と、何かをしようとする狙いを区別'],
 '113-04':['論破','意図','人を惑わす不正確な議論と、何かをしようとする狙いを区別'],
 '114-04':['伝達','影響','出来事のその後を知らせる報道と、働きが他に及ぼす変化を区別'],
 '124-02':['含意','伝達','内容を文章にはっきり示すことと、情報・意思を相手に届けることを区別'],
 '124-04':['暗黙','含意','文字どおりの意味と、表面にないが読み取れる意味を区別']
};
const replacementLog=[];
for(const q of after){
 if(q.question_type==='meaning'){
  const words=q.choices.map(d=>oldWords[d]);
  if(words.some(w=>!w))throw Error(q.id+' unknown definition');
  const edit=replacements[q.id.slice(4,-2)];
  if(edit){const [from,to,reason]=edit, i=words.indexOf(from);if(i<0||i===q.correct_index)throw Error(q.id+' invalid replacement');words[i]=to;replacementLog.push([q.id,i+1,from,to,reason]);}
  q.choices=words.map(w=>definitions[w]);q.correct_answer=q.choices[q.correct_index];
  const wrong=words.filter((_,i)=>i!==q.correct_index);
  q.explanation=`「${q.target_word}」は${definitions[q.target_word]}。一方、「${wrong[0]}」は${definitions[wrong[0]]}。また、「${wrong[1]}」は${definitions[wrong[1]]}。それぞれの意味の中心を比べて区別しよう。`;
 }else if(q.question_type==='context'){
  // Replace exact word/definition pairs, preserving every scene and individual rationale.
  for(const w of q.choices)q.explanation=q.explanation.replaceAll('「'+w+'」は'+originalDefs[w],'「'+w+'」は'+definitions[w]);
 }
}
const q=after.find(q=>q.id==='JLR-005-01');
q.prompt=q.prompt.slice(0,q.prompt.indexOf('【問い】'))+'【問い】\n「十人増えた」という数字の印象を判断するために、本文が確認したいとしているものは何か。';
q.choices=['今年の参加者が去年より増えたという事実','去年の参加者の人数','「大人気になった」と話した人の数'];q.correct_answer=q.choices[q.correct_index];
q.explanation='根拠：最終文「もとの人数も確認したい」。誤答1：増えたことはすでに本文にある。誤答3：話した人がいたことは書かれているが、その人数は本文が確認したいとしているものではない。';
const csvCell=x=>'"'+String(x??'').replaceAll('"','""')+'"';
const csv=(headers,rows)=>[headers,...rows].map(r=>r.map(csvCell).join(',')).join('\r\n')+'\r\n';
const fields=[...new Set(after.flatMap(Object.keys))];
const columns=fields.filter(k=>!['choices','correct_index'].includes(k));columns.splice(columns.indexOf('correct_answer'),0,'choice_1','choice_2','choice_3','correct_option');columns.push('present_fields');
const row=q=>columns.map(k=>k==='present_fields'?Object.keys(q).join(';'):k==='correct_option'?q.correct_index+1:/^choice_[123]$/.test(k)?q.choices[Number(k.at(-1))-1]:q[k]??'');
const changes=[];
for(let i=0;i<before.length;i++)for(const k of fields){if(JSON.stringify(before[i][k])===JSON.stringify(after[i][k]))continue;changes.push([after[i].id,k,JSON.stringify(before[i][k]),JSON.stringify(after[i][k]),after[i].id==='JLR-005-01'?'Claude第5回監査本文の完成修正':replacements[after[i].id.slice(4,-2)]?'正答だけ型が異なる設問の誤答差し替え／現行定義と解説の連動更新':'定義の語尾統一・個別修正の全使用箇所への連動更新']);}
const write=(p,s)=>fs.writeFile(path.join(root,p),s);
await fs.mkdir(path.join(root,'data/v6'),{recursive:true});
await write('data/v6/questions.json',JSON.stringify(after,null,2)+'\n');await write('data/v6/questions.csv',csv(columns,after.map(row)));
await write('data/v6/change_map_v5_v6.csv',csv(['id','field','before','after','reason'],changes));
await write('data/v6/definition_changes.csv',csv(['word','before','after','source'],Object.entries(definitions).filter(([w,d])=>d!==originalDefs[w]).map(([w,d])=>[w,originalDefs[w]||'水滴が落ちてこない霧のこと',d,'ChatGPT制作側再抽出・編集。Claude CSV原本ではない'])));
await write('data/v6/distractor_replacements.csv',csv(['id','choice_number','before_word','after_word','selection_reason'],replacementLog));
await write('data/v6/changed_ids.csv',csv(['id','question_type','changed_fields'],after.flatMap((q,i)=>{const keys=fields.filter(k=>JSON.stringify(q[k])!==JSON.stringify(before[i][k]));return keys.length?[[q.id,q.question_type,keys.join(';')]]:[]})));
console.log(JSON.stringify({questions:after.length,fields:changes.length,ids:new Set(changes.map(x=>x[0])).size,replacements:replacementLog.length},null,2));
