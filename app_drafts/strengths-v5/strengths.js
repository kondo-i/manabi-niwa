/* Choice-led continuation; a few answers never label a child's ability. */
(function(root){'use strict';
const subjects=['japanese','math','english','social','science'];
function activeSubject(state,units,explicit){
 if(subjects.includes(explicit))return explicit;
 if(subjects.includes(state.focusSubject))return state.focusSubject;
 const last=units.find(u=>u.id===state.lastUnitId);if(last)return last.subject;
 const record=Object.values(state.records||{}).filter(r=>!r.isStretch&&units.some(u=>u.id===r.unitId)).sort((a,b)=>(b.lastDate||'').localeCompare(a.lastDate||''))[0];
 return units.find(u=>u.id===record?.unitId)?.subject||'';
}
function continuation(state,units,explicit){
 const subject=activeSubject(state,units,explicit),pool=units.filter(u=>u.subject===subject);
 if(!pool.length)return null;
 const record=Object.values(state.records||{}).filter(r=>!r.isStretch&&pool.some(u=>u.id===r.unitId)).sort((a,b)=>(b.lastDate||'').localeCompare(a.lastDate||''))[0];
 return pool.find(u=>u.id===state.lastUnitId)||pool.find(u=>u.id===record?.unitId)||pool.find(u=>u.grade===1)||pool[0];
}
function otherSubjects(state,units,explicit){const active=activeSubject(state,units,explicit);return subjects.filter(s=>s!==active&&units.some(u=>u.subject===s));}
function validateBank(bank){
 if(!Array.isArray(bank)||!bank.length)throw Error('チャレンジの問題を確認できません');
 const ids=new Set();for(const q of bank){if(!q.id||ids.has(q.id)||!subjects.includes(q.subject)||!Number.isInteger(q.grade)||q.grade<1||q.grade>3||!q.prompt||q.type!=='choice'||q.choices?.length!==3||new Set(q.choices).size!==3||!Number.isInteger(q.answer)||q.answer<0||q.answer>2||!q.explanation||q.hints?.length!==2||q.hints.some(h=>typeof h!=='string'||!h)||q.auditStatus!=='independent_review_pending')throw Error('チャレンジの問題データを確認できません');ids.add(q.id);}return bank;
}
function choose(bank,subject,records={},grade=0,previousId=''){
 let options=bank.filter(q=>q.subject===subject&&(!grade||q.grade<=grade));
 if(options.length>1)options=options.filter(q=>q.id!==previousId);
 const attempts=q=>Number.isFinite(records[q.id]?.attempts)?Math.max(0,records[q.id].attempts):0;
 const lastAt=q=>{const value=records[q.id]?.lastAt;if(Number.isFinite(value))return value;const parsed=typeof value==='string'?Date.parse(value):NaN;return Number.isFinite(parsed)?parsed:0;};
 options.sort((a,b)=>Number(attempts(a)>0)-Number(attempts(b)>0)
  ||String(records[a.id]?.lastDate||'').localeCompare(String(records[b.id]?.lastDate||''))
  ||attempts(a)-attempts(b)||lastAt(a)-lastAt(b)||String(a.id).localeCompare(String(b.id),undefined,{numeric:true}));
 return options[0]||null;
}
function nextAttemptAt(records,now=Date.now()){
 const times=Object.values(records||{}).map(r=>r.lastAt).filter(Number.isFinite);
 return Math.max(Number.isFinite(now)?now:0,times.length?Math.max(...times)+1:0);
}

const api={subjects,activeSubject,continuation,otherSubjects,validateBank,choose,nextAttemptAt};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Strengths=api;
})(typeof window!=='undefined'?window:globalThis);
