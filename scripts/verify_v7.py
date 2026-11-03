"""Independent read-back verification, separate from builder."""
import csv,json,pathlib,hashlib,collections
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def rows(p):
 with (R/p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
old=read('data/v6/questions.json');qs=read('data/v7/questions.json');checks=[]
def check(n,ok):
 assert ok,n
 checks.append({'name':n,'status':'PASS'})
check('1040 unique IDs, same order',len(qs)==1040 and len({q['id'] for q in qs})==1040 and [q['id'] for q in qs]==[q['id'] for q in old])
check('CSV all fields and types exactly reconstructed',[{k:json.loads(v) for k,v in row.items() if v!=''} for row in rows('data/v7/questions.csv')]==qs)
check('three distinct choices and correct answer',all(len(q['choices'])==len(set(q['choices']))==3 and type(q['correct_index'])==int and 0<=q['correct_index']<3 and q['choices'][q['correct_index']]==q['correct_answer'] for q in qs))
m=[q for q in qs if q['question_type']=='meaning'];c=[q for q in qs if q['question_type']=='context'];l=[q for q in qs if q['question_type']=='logical_reading']
check('500 M, 500 C, 40 reading',[len(m),len(c),len(l)]==[500,500,40])
check('all 500 M same ending type; all 1500 choices end in こと',all(len({d.endswith('であること') for d in q['choices']})==1 and all(d.endswith('こと') for d in q['choices']) for q in m))
defs={q['target_word']:q['correct_answer'] for q in m};defs['霧']='細かな水滴が空気中に浮かんで、視界が白くかすむこと';names={d:w for w,d in defs.items()}
check('canonical definitions unique and manifest matches',len(names)==501 and read('data/v7/canonical_definitions.json')==defs)
check('M current word names and definitions in explanations',all(d in q['explanation'] and f'「{names[d]}」' in q['explanation'] for q in m for d in q['choices']))
check('C all three current definitions linked',all(f'「{w}」は{defs[w]}' in q['explanation'] for q in c for w in q['choices']))
actual={(b['id'],k,json.dumps(a[k],ensure_ascii=False,sort_keys=True),json.dumps(b[k],ensure_ascii=False,sort_keys=True)) for a,b in zip(old,qs) for k in a if a[k]!=b[k]}
cm=rows('data/v7/change_map_v6_v7.csv');listed={(r['id'],r['field'],json.dumps(json.loads(r['before']),ensure_ascii=False,sort_keys=True),json.dumps(json.loads(r['after']),ensure_ascii=False,sort_keys=True)) for r in cm}
check('change map exact IDs fields before after; no missing or extra entries',actual==listed and len(cm)==len(listed))
protected=['id','grade','grade_policy','furigana_policy','passage','prompt','correct_index','review_status','claude_audit','release_status']
check('protected fields preserved; no inherited audit statuses overwritten',all(a.get(k)==b.get(k) for a,b in zip(old,qs) for k in protected))
check('all reading data unchanged',all(a==b for a,b in zip(old,qs) if a['question_type']=='logical_reading'))
repl=rows('data/v7/distractor_replacements.csv');byid={q['id']:q for q in qs};oldby={q['id']:q for q in old}
# Check independently against old dictionary, including every before value.
od={q['target_word']:q['correct_answer'] for q in old if q['question_type']=='meaning'};od['霧']=defs['霧']
check('replacement log before/after values and explanation exact',len(repl)==117 and len({(r['id'],r['choice_number']) for r in repl})==117 and all(int(r['choice_number'])-1!=byid[r['id']]['correct_index'] and oldby[r['id']]['choices'][int(r['choice_number'])-1]==od[r['before_word']] and byid[r['id']]['choices'][int(r['choice_number'])-1]==defs[r['after_word']] and r['after_word'] in byid[r['id']]['explanation'] and defs[r['after_word']] in byid[r['id']]['explanation'] for r in repl))
check('requested 061,047,059 replacements',all(defs[w] in byid[i]['choices'] for i,words in [('JVQ-061-04-M',['中断','進展']),('JVQ-047-04-M',['仮説']),('JVQ-059-04-M',['選挙'])] for w in words) and defs['国際']=='国と国との間で行われること')
result={'status':'MECHANICAL_PASS_SEMANTIC_REAUDIT_PENDING','questions':1040,'changed_fields':len(actual),'changed_questions':len({a[0] for a in actual}),'changed_by_type':dict(collections.Counter(byid[i]['question_type'] for i in {a[0] for a in actual})),'mixed_before':sum(len({d.endswith('であること') for d in q['choices']})>1 for q in old if q['question_type']=='meaning'),'mixed_after':0,'distractor_choices_replaced':117,'definition_changes':3,'checks':checks,'Claude_CSV_provided':False,'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'data/v7').iterdir() if p.is_file()}}
(R/'reports/v7_verification_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','hashes']},ensure_ascii=False))
