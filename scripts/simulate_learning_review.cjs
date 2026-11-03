/* Read-only app review: actual application JS and click handlers with a DOM/storage substitute. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const root=path.resolve(process.argv[2]||'.'), dist=path.join(root,'dist'), dest=path.join(__dirname,'../reports/app_review');
let seed=20261103;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const raw=p=>fs.readFileSync(path.join(root,p));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const write=(p,x)=>fs.writeFileSync(path.join(dest,p),JSON.stringify(x,null,2)+'\n');
const catalog=json('dist/data/catalog.json'),C=require(path.join(dist,'content.js'));
const bank=json('dist/data/stretch-bank.json');
const base={records:{},days:[],completed:[],xp:0,session:null};
const tick=async()=>{for(let i=0;i<18;i++)await new Promise(resolve=>setImmediate(resolve));};
async function browser(saved=base){
 let html='',data=JSON.stringify(saved);const listeners={};
 const app={set innerHTML(v){html=v},get innerHTML(){return html},querySelectorAll(){return []}};
 const g={console,crypto:crypto.webcrypto,FormData:class{constructor(form){this.form=form;}get(k){return this.form[k];}},window:{scrollTo(){}},document:{getElementById:id=>id==='app'?app:{},querySelectorAll:()=>[],addEventListener:(ev,cb)=>{listeners[ev]=cb;}},localStorage:{getItem:()=>data,setItem:(_,v)=>{data=v}},fetch:async f=>({ok:true,json:async()=>json('dist/'+f.split('?')[0])})};
 for(const [symbol,file] of Object.entries({Content:'content',Strengths:'strengths',Growth:'progress',GardenCamp:'garden-camp',RPG:'rpg',RepairScene:'repair-scene',Adventure:'adventure-routes',DensityLab:'density-lab',LightLab:'light-lab',SpringLab:'spring-lab',Journey:'journey',Routing:'routes'}))g[symbol]=require(path.join(dist,file+'.js'));
 const ctx=vm.createContext(g);for(const file of ['strength-ui.js','app.js'])vm.runInContext(raw('dist/'+file).toString('utf8'),ctx);await tick();
 const nav=raw('dist/index.html').toString('utf8').match(/<nav>[\s\S]*?<\/nav>/)?.[0]||'';
 const buttons=()=>[...(nav+html).matchAll(/<button\b([^>]*)>(.*?)<\/button>/gs)].map(m=>{const dataset=Object.fromEntries([...m[1].matchAll(/data-([\w-]+)="([^"]*)"/g)].map(a=>[a[1],a[2]]));return {dataset,disabled:/\bdisabled\b/.test(m[1]),label:m[2].replace(/<[^>]*>/g,'').trim()};});
 return {get html(){return html},get saved(){return JSON.parse(data)},buttons,async click(d){const b=buttons().find(b=>!b.disabled&&Object.entries(d).every(([k,v])=>b.dataset[k]===String(v)));assert(b,`Button missing ${JSON.stringify(d)}`);listeners.click({target:{closest:()=>b}});await tick();return b.label;},async submit(answer){assert(html.includes('id="typed-answer"'));listeners.submit({target:{id:'typed-answer',answer},preventDefault(){}});await tick();}};
}
async function main(){
 fs.mkdirSync(dest,{recursive:true});
 const commit=execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
 const groups=['balance','cozy'].map(g=>({g,units:json(`docs/${g}-manifest.json`).newUnits}));
 C.validateCatalog(catalog);const ids=new Set(),files=new Set(),added=[];
 for(const {g,units} of groups)for(const unitId of units){const u=catalog.units.find(u=>u.id===unitId);assert(u,unitId);
  for(const p of u.packs){const qs=json('dist/'+p.file);files.add('dist/'+p.file);C.validatePack(qs,u,p);
   for(const q of qs){assert(!ids.has(q.id)&&q.prompt&&q.explanation,q.id);ids.add(q.id);if(q.type==='choice'){assert.equal(new Set(q.choices).size,q.choices.length);assert(C.judge(q,q.answer));q.choices.forEach((_,i)=>{if(i!==q.answer)assert(!C.judge(q,i),q.id);});}added.push({batch:g,unit_id:u.id,unit_title:u.title,subject:u.subject,grade:u.grade,source_file:'dist/'+p.file,question:q});}
  }
 }
 require(path.join(dist,'strengths.js')).validateBank(bank);files.add('dist/data/stretch-bank.json');
 for(const q of bank){assert(!ids.has(q.id));ids.add(q.id);added.push({batch:'stretch',subject:q.subject,grade:q.grade,source_file:'dist/data/stretch-bank.json',question:q});}
 const counts={};for(const a of added){counts[a.batch]=(counts[a.batch]||0)+1;}
 assert.deepEqual(counts,{balance:100,cozy:60,stretch:25});write('added_185_questions.json',added);
 const amendments=[
  ['japanese-g2-auxiliary-context-balance-001:q6','P1','「起きよう」の助動詞は「よう」。設問の引用単位が誤り。','「私は明日こそ早く起きよう」の「よう」が表す意味はどれか。','「起き」に付く「よう」は、ここでは自分が早く起きるつもりだという意志を表す。伝聞や打ち消しではない。'],
  ['japanese-g2-evidence-compare-balance-001:q1','P2','両店が文房具しか売っていない場合、対象の種類が同じになる。','二つの店はどちらも文房具とお菓子を売っている。店Aは「全品10％引き」、店Bは「文房具だけ20％引き」。この二つの案内から分かることは？','Aでは文房具もお菓子も値引きされる。Bで値引きされるのは文房具。元の値段が分からないので、どちらで安く買えるかは決められない。'],
  ['japanese-g2-honorific-context-balance-001:q1','P2','先生本人の発言に尊敬語を当てはめる読みを避ける。','生徒が友達に「明日、先生が教室に行きます」と伝えます。先生の動作を高める言い方にすると、「行きます」はどれに変わる？','動作をするのは先生なので、尊敬語の「いらっしゃいます」を使う。「参ります」は自分側の動作をへりくだって述べる形。「申します」は「言う」の謙譲語。'],
  ['japanese-g2-honorific-context-balance-001:q9','P3','来客相手の内・外の関係に依存するため、話者と相手を固定。','生徒が友達に「先生は今、教室にいる」と説明します。先生への敬意が伝わる言い方はどれ？','「いる」の尊敬語は「いらっしゃる」。「申す」は「言う」、「拝見する」は「見る」の謙譲語。'],
  ['japanese-g2-story-feelings-cozy-001:q4','P2','足音は直接の描写、静けさはそこから伝わる様子。','「帰り道、足音だけが長い廊下に響いた。」この一文から、どんな様子が伝わってくる？','足音だけが響く描写から、廊下の静けさが伝わる。合唱も温度の数値も書かれていない。'],
  ['science-g1-kitchen-notebook-cozy-001:q8','P3','比較する液体の初期量もそろえる。','同じ材質・同じ形の容器を二つ用意した。それぞれに同じ種類・同じ量の液体を入れ、一方にだけふたをする。何の違いを比べる実験？','容器の材質と形、中の液体の種類と量は同じ。変えるのは、ふたをするかどうか。'],
  ['social-g3-civics-discussion-balance-001:q7','P3','夜勤の人が昼間に参加しやすいという一般化を避ける。','【架空の意見募集】昼の説明会には「昼間なら来られる」という人も、「仕事で昼間は来られない」という人もいます。もっと参加しやすくするには？','別の時間にも説明会を開いたり、書面で意見を出せるようにしたりすると、参加できる人が増える。来られないことと、意見がないことは別。']
 ];
 const changes=amendments.map(([id,priority,reason,prompt,explanation])=>{const item=added.find(a=>a.question.id===id);assert(item,id);const before=item.question,after={...before,prompt,explanation};assert(C.judge(after,before.answer)&&prompt!==before.prompt&&explanation!==before.explanation);return {id,priority,reason,source_file:item.source_file,before,after,status:'proposal_only_not_deployed'};});
 assert.equal(new Set(changes.map(q=>q.id)).size,7);write('proposed_question_changes.json',changes);
 const steps=[];let b=await browser();
 const first=b.buttons().filter(x=>x.dataset.action==='focus-subject');assert.equal(first.length,5);assert(!b.buttons().some(x=>x.dataset.action==='stretch-start'));
 const firstChoices=first.map(x=>x.dataset.item);
 await b.click({action:'focus-subject',item:'japanese'});
 const warm=b.buttons().find(x=>x.dataset.action==='warmup');assert(warm);await b.click({action:'warmup',unit:warm.dataset.unit});
 let s=b.saved.session,q=s.questions[0];assert.equal(s.subject,'japanese');assert.equal(s.ids.length,1);
 const id=q.id;const respond=async(q,correct)=>q.type==='choice'?b.click({answer:correct?q.answer:(q.answer+1)%q.choices.length}):b.submit(correct?String(q.answers?.[0]??q.answer):'999999');
 await respond(q,false);assert(b.html.includes(q.explanation));await b.click({action:'next'});
 const result={score:b.saved.session.score,total:b.saved.session.ids.length,xp:b.saved.xp,effort_message:b.html.includes('考えた時間も、きみの一歩。'),direct_retry:b.buttons().some(x=>x.dataset.action==='review')};
 assert.equal(result.score,0);assert(result.effort_message);await b.click({action:'finish'});
 assert(b.html.includes('国語の続きから'));const others=b.buttons().filter(x=>x.label.includes('ものぞいてみる')).map(x=>x.dataset.item);assert.equal(others.length,4);
 steps.push({scenario:'初回から国語を1問。誤答しても国語へ戻る',firstChoices,taps_to_question:2,id,result,continuation:'japanese',other_subjects:others});
 await b.click({page:'review'});const review=b.buttons().find(x=>x.dataset.action==='review'&&x.dataset.unit===warm.dataset.unit);assert(review);await b.click(review.dataset);q=b.saved.session.questions[0];assert.equal(q.id,id);await respond(q,true);await b.click({action:'next'});assert.equal(b.saved.records[id].lastCorrect,true);
 steps.push({scenario:'誤答後に復習で取り戻す',id,taps_from_result_to_review:3,correct_on_retry:b.saved.records[id].lastCorrect});
 await b.click({action:'finish'});await b.click({action:'focus-subject',item:'math'});await b.click({action:'stretch-start',item:'math'});
 assert(b.html.includes('できなくても大丈夫'));await b.click({action:'stretch-hint'});await b.click({action:'stretch-hint'});b=await browser(b.saved);assert.equal(b.saved.session.hintCount,2);assert(b.html.includes('ヒント2'));
 q=b.saved.session.questions[0];await b.click({answer:q.answer});await b.click({action:'next'});const r=b.saved.records[q.id];assert.equal(r.correct,0);assert.equal(r.assistedCorrect,1);
 steps.push({scenario:'数学に寄り道。難問でヒント2回、再読込後に正解',id:q.id,hints:2,self_correct:r.correct,assisted_correct:r.assistedCorrect,xp:b.saved.xp});
 await b.click({action:'finish'});await b.click({action:'stretch-start',item:'math'});q=b.saved.session.questions[0];await b.click({action:'stretch-solution'});await b.click({action:'next'});const view=b.saved.records[q.id];assert.equal(view.correct,0);assert.equal(view.lastCorrect,null);assert(b.html.includes('自力正解には数えません'));
 steps.push({scenario:'難問を解けないとき、解説だけで終える',id:q.id,solution_views:view.solutionViews,self_correct:view.correct,finished:b.saved.session.finished});
 await b.click({action:'finish'});await b.click({action:'focus-subject',item:'social'});
 const replay=[];for(let i=0;i<7;i++){await b.click({action:'stretch-start',item:'social'});const q=b.saved.session.questions[0];replay.push(q.id);await b.click({action:'stretch-solution'});await b.click({action:'next'});await b.click({action:'finish'});}
 assert.equal(new Set(replay.slice(0,5)).size,5);
 steps.push({scenario:'同じ日に社会の難問を一巡後、さらに2回開く',ids:replay,repeat_after_cycle:replay[5]===replay[6]});
 const fileInfo=[...files].sort().map(p=>({path:p,sha256:sha(raw(p))}));
 if(process.argv.includes('--check-live'))for(const f of fileInfo){const response=await fetch('https://kondo-study-lab.vast-stone-7426.chatgpt.site/'+f.path.slice(5));if(!response.ok)throw Error(f.path+' '+response.status);f.live_sha256=sha(Buffer.from(await response.arrayBuffer()));assert.equal(f.live_sha256,f.sha256,f.path);}
 write('simulation_results.json',{source_commit:commit,random_seed:20261103,method:'Actual click-handler code; simulated DOM, storage and learner answers; no student trial or timing claim',counts,checks:{unique_ids:ids.size,proposed_changes:changes.length,live_assets_compared:process.argv.includes('--check-live')?fileInfo.length:0},asset_files:fileInfo,scenarios:steps});
 console.log(JSON.stringify({commit,counts,live_assets_compared:process.argv.includes('--check-live')?fileInfo.length:0,steps},null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
