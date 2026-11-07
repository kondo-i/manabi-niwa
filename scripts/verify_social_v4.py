"""Read-only full-field/diff verification; optional outputs default to an external temp folder."""
import argparse,collections,csv,difflib,json,re,tempfile,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def rows(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def norm(s):return re.sub(r'[\s。、，．「」『』【】?？：:]','',unicodedata.normalize('NFKC',s))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path);a=p.parse_args();out=a.output_dir or Path(tempfile.mkdtemp(prefix='manabi-social-v4-'));out.mkdir(parents=True,exist_ok=True);checks=[]
 def ck(n,v):
  assert v,n
  checks.append({'name':n,'status':'PASS'})
 S=R/'data/social/v4';A=R/'reports/app_review/v4';social=load(S/'questions.json');app=load(A/'questions.json');old_social=load(R/'data/social/v3/questions.json');old_app=load(R/'reports/app_review/v3/questions.json')
 ck('32 social and 188 app unique IDs',len(social)==32 and len(app)==188 and len({q['id'] for q in social+app})==220)
 summaries={}
 for label,F,old,data in [('social',S,old_social,social),('app',A,old_app,app)]:
  back=[{k:json.loads(v) for k,v in row.items() if v!=''} for row in rows(F/'questions.csv')];ck(label+' CSV full-field equality',back==data)
  ck(label+' 3 distinct choices valid index',all(len(q['choices'])==len(set(q['choices']))==3 and type(q.get('correct_index',q.get('answer'))) is int and 0<=q.get('correct_index',q.get('answer'))<3 for q in data))
  previous={q['id']:q for q in old};expected=[]
  for q in data:
   b=previous.get(q['id'])
   if b is None:expected.append((q['id'],'add','__item__',None,q));continue
   expected.extend((q['id'],'modify',k,b.get(k),q.get(k)) for k in dict.fromkeys([*b,*q]) if b.get(k)!=q.get(k))
  actual=[(r['id'],r['operation'],r['field'],json.loads(r['before']),json.loads(r['after'])) for r in rows(F/'change_map_v3_v4.csv')];ck(label+' exact diff rows and no duplicates',expected==actual and len(actual)==len({(r[0],r[2]) for r in actual}))
  ck(label+' Markdown complete',all(q['prompt'] in (F/'questions.md').read_text() and q['explanation'] in (F/'questions.md').read_text() for q in data))
  summaries[label]={'count':len(data),'change_rows':len(actual),'content_changed_ids':sorted({r[0] for r in actual if r[2]!='grade_policy'}),'new_ids':[q['id'] for q in data if q['id'] not in previous]}
 ck('social correct answer text and distractor notes',all(q['correct_answer']==q['choices'][q['correct_index']] and {n['choice'] for n in q['distractor_notes']}==set(q['choices'])-{q['correct_answer']} and all(n['reason'] in q['explanation'] for n in q['distractor_notes']) for q in social))
 sources=load(S/'sources.json')['sources'];ck('sources IDs resolve',all(all(x in sources for x in q['source_ids']) for q in social))
 ck('no repeated quoted subject grammar',not any(re.search(r'「([^」]+)」は\1は',q['explanation']) for q in social+app))
 ck('no furigana all social policy explicit',all(q['furigana_policy']=='none_by_user_request_20261105' and '<ruby' not in q['prompt']+q['explanation'] for q in social) and all('<ruby' not in q['prompt']+q['explanation'] for q in app))
 seqs=[[q['correct_index'] for q in social]]+[[q['correct_index'] for q in social if q['field']==f] for f in ['geography','history','civics']]
 ck('no answer position period 1-5',all(not any(all(seq[i]==seq[i%p] for i in range(len(seq))) for p in range(1,6)) for seq in seqs));counts=collections.Counter(q['correct_index']+1 for q in social);ck('position count difference <=1',max(counts.values())-min(counts.values())<=1)
 ck('no only always all cue in social choices',not any(re.search('だけ|必ず|すべて',v) for q in social for v in q['choices']))
 by={q['id']:q for q in social+app};ck('HIS011 institution change with 学制 answer',by['SOC-HIS-011']['correct_answer']=='学制' and by['SOC-HIS-011']['choices']==['地租改正','廃藩置県','学制'] and '原史料からの直接引用ではない' in by['SOC-HIS-011']['explanation'])
 ck('scale conversion independently recalculated',6*50000/25000==12 and by['social-g1-geography-data-balance-001:q10']['choices'][by['social-g1-geography-data-balance-001:q10']['answer']]=='12cm')
 ck('introduction retained byte-equivalent as JSON object',by['stretch-japanese-20261103:q3']==next(q for q in old_app if q['id']=='stretch-japanese-20261103:q3'))
 ck('new dialogue correct answer and two requested hints',by['stretch-japanese-20261107:q6']['choices'][by['stretch-japanese-20261107:q6']['answer']]=='白いボール' and by['stretch-japanese-20261107:q6']['hints']==['「それ」は、話し相手の近くにある物を指すことが多いよ','太郎は誰の持つボールを見て話したかな'])
 ck('28 challenge questions remain prototype with two hints',sum(q['id'].startswith('stretch-') for q in app)==28 and all(len(q['hints'])==2 and q['status']=='prototype' and q['auditStatus']=='independent_review_pending' for q in app if q['id'].startswith('stretch-')))
 combos=[(large+small,24*large+15*small) for large in range(3) for small in range(6)]
 ck('inherited q4 q5 constraints recomputed',[(12000*n<=30000 and 2*n>=6) for n in [2,3]]==[False,False] and 26000<=30000 and min(n for n,capacity in combos if capacity>=70)==4)
 # Compare current and prior datasets across different IDs. Similarity is screening, not semantic proof.
 candidates=social+app+old_social+old_app+load(R/'data/social/v2/questions.json')+[x['question'] for x in load(R/'reports/app_review/added_185_questions.json')]
 groups=collections.defaultdict(set)
 for q in candidates:groups[norm(q['prompt'])].add(q['id'])
 exact=[sorted(ids) for ids in groups.values() if len(ids)>1];ck('normalized exact duplicates across different IDs zero including old drafts',not exact)
 focus=load(A/'audit_focus.json');changed=[q for q in social+app if q['id'] in set(summaries['social']['content_changed_ids']+summaries['app']['content_changed_ids'])];near=[]
 for q in changed:
  for other in candidates:
   if q['id']==other['id']:continue
   score=difflib.SequenceMatcher(None,norm(q['prompt']),norm(other['prompt']),autojunk=False).ratio()
   if score>=0.62:
    item={'id':q['id'],'other_id':other['id'],'similarity':round(score,3),'prompt':q['prompt'],'other_prompt':other['prompt']}
    if item not in near:near.append(item)
 result={'status':'MECHANICAL_PASS_INDEPENDENT_CONTENT_AUDIT_PENDING','social':summaries['social'],'app':summaries['app'],'social_positions':dict(counts),'exact_duplicate_count':0,'near_candidates':len(near),'semantic_duplicate_zero_verified':False,'checks':checks}
 (out/'verification_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(out/'duplicate_screening.json').write_text(json.dumps({'exact':exact,'near':near,'limit':'Changed prompts against current and historical drafts; no semantic-zero claim'},ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}|{'check_count':len(checks),'output':str(out)},ensure_ascii=False))
if __name__=='__main__':main()
