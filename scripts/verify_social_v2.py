"""Independent read-back and answer-position validation."""
import collections,csv,hashlib,json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[1];D=R/'data/social/v2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
old=read(R/'data/social/v1/questions.json');qs=read(D/'questions.json');sources=read(D/'sources.json')['sources'];checks=[]
def check(name,ok):
 assert ok,name
 checks.append({'name':name,'status':'PASS'})
check('30 unique IDs in original order and 10 per field',len(qs)==len({q['id'] for q in qs})==30 and [q['id'] for q in old]==[q['id'] for q in qs] and collections.Counter(q['field'] for q in qs)=={'geography':10,'history':10,'civics':10})
recovered=[]
for r in rows(D/'questions.csv'):
 for k in ['choices','distractor_notes','source_ids']:r[k]=json.loads(r[k])
 for k in ['grade','correct_index']:r[k]=int(r[k])
 recovered.append(r)
check('CSV full-field reverse roundtrip',recovered==qs)
check('distinct choices and correct index and answer',all(len(q['choices'])==len(set(q['choices']))==3 and all(q['choices']) and type(q['correct_index'])==int and 0<=q['correct_index']<3 and q['choices'][q['correct_index']]==q['correct_answer'] for q in qs))
check('each distractor has a matching explanation and note',all(len(q['distractor_notes'])==2 and {n['choice'] for n in q['distractor_notes']}==set(q['choices'])-{q['correct_answer']} and all(n['choice'] in q['explanation'] and n['reason'] in q['explanation'] for n in q['distractor_notes']) for q in qs))
check('all source references and publication/grade flags',all(q['source_ids'] and all(s in sources and sources[s]['url'].startswith('https://') for s in q['source_ids']) and q['release_status']=='not_published' and q['grade']==a['grade'] for q,a in zip(qs,old)))
actual={(b['id'],k,json.dumps(a[k],sort_keys=True),json.dumps(b[k],sort_keys=True)) for a,b in zip(old,qs) for k in a if a[k]!=b[k]}
rr=rows(D/'change_map_social_v1_v2.csv');listed={(r['id'],r['field'],json.dumps(json.loads(r['before']),sort_keys=True),json.dumps(json.loads(r['after']),sort_keys=True)) for r in rr}
check('change map before/after values exact',actual==listed and len(rr)==len(listed))
positions={f:[q['correct_index']+1 for q in qs if q['field']==f] for f in ['geography','history','civics']}
check('each correct position occurs 10 times',collections.Counter(q['correct_index'] for q in qs)=={0:10,1:10,2:10})
check('no global or within-field periods of length 1 to 5',all(not any(all(v[i]==v[i%p] for i in range(len(v))) for p in range(1,6)) for v in [list(positions['geography']+positions['history']+positions['civics']),*positions.values()]))
limited=[{'id':q['id'],'choice':c,'correct':c==q['correct_answer']} for q in qs for c in q['choices'] if re.search('だけ|必ず|すべて',c)]
check('no only/always/all cue in choices',limited==[])
by={q['id']:q for q in qs}
check('three scale calculations and scale range comparison',by['SOC-GEO-007']['correct_answer']==f'{2*25000//100}m' and by['SOC-GEO-008']['correct_answer']==f'{3*50000/100000:g}km' and by['SOC-GEO-009']['correct_answer']==f'{100000//25000}cm' and by['SOC-GEO-010']['correct_answer']=='狭い範囲を、より大きく表せる' and 25000/50000==0.5)
check('HIS-010 content replaced, not copied from HIS-008',by['SOC-HIS-010']['correct_answer']=='天皇' and 'MEIJI_CONST' in by['SOC-HIS-010']['source_ids'] and by['SOC-HIS-008']['correct_answer']=='1947年')
md=(D/'questions.md').read_text(encoding='utf-8');check('Markdown contains all IDs prompts choices and exact answers',all(f'## {q["id"]}\n' in md and q['prompt'] in md and all(c in md for c in q['choices']) and f'正答：{q["correct_index"]+1}. {q["correct_answer"]}' in md for q in qs))
result={'status':'MECHANICAL_PASS_REAUDIT_PENDING','questions':30,'content_edits':7,'changed_questions':len({i for i,k,a,b in actual}),'changed_fields':len(actual),'position_changed_ids':[b['id'] for a,b in zip(old,qs) if a['correct_index']!=b['correct_index']],'positions':positions,'limited_choice_matches':limited,'checks':checks,'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.is_file()}}
(R/'reports/social_v2_verification_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','hashes']},ensure_ascii=False))
