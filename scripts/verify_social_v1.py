"""Independent mechanical validation; not a semantic or Claude audit."""
import collections,csv,hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent.parent
folder=root/'data/social/v1'
q=json.loads((folder/'questions.json').read_text());sources=json.loads((folder/'sources.json').read_text())['sources'];checks=[]
def check(name,test):
 assert test,name
 checks.append({'name':name,'status':'PASS'})
check('30 items and unique IDs',len(q)==len({x['id'] for x in q})==30)
check('10 per field',collections.Counter(x['field'] for x in q)=={'geography':10,'history':10,'civics':10})
check('unique prompts',len({x['prompt'] for x in q})==30)
check('three distinct nonempty choices',all(len(x['choices'])==len(set(x['choices']))==3 and all(x['choices']) for x in q))
check('index and correct answer',all(type(x['correct_index']) is int and 0<=x['correct_index']<3 and x['choices'][x['correct_index']]==x['correct_answer'] for x in q))
check('exactly 2 distractor notes, for wrong choices only',all(len(x['distractor_notes'])==2 and {d['choice'] for d in x['distractor_notes']}==set(x['choices'])-{x['correct_answer']} and all(d['reason'] in x['explanation'] for d in x['distractor_notes']) for x in q))
check('source links resolve in manifest',all(x['source_ids'] and all(s in sources and sources[s]['url'].startswith('https://') for s in x['source_ids']) for x in q))
check('all drafts and unpublished',all(x['review_status']=='draft_awaiting_claude_independent_review' and x['release_status']=='not_published' for x in q))
rows=list(csv.DictReader((folder/'questions.csv').open(newline='')))
back=[]
for row in rows:
 for key in ['choices','distractor_notes','source_ids']:row[key]=json.loads(row[key])
 for key in ['grade','correct_index']:row[key]=int(row[key])
 back.append(row)
check('CSV full-field reverse round trip',back==q)
check('answer positions balanced',collections.Counter(x['correct_index'] for x in q)=={0:12,1:9,2:9})
# Expected arithmetic is computed independently of the authored explanation strings.
expect={'SOC-GEO-007':f'{2*25000//100}m','SOC-GEO-008':f'{3*50000/100000:g}km','SOC-GEO-009':f'{100000//25000}cm'}
check('scale calculations',all(next(x for x in q if x['id']==key)['correct_answer']==value for key,value in expect.items()))
check('markdown contains all prompts and answers',all(x['prompt'] in (folder/'questions.md').read_text() and x['correct_answer'] in (folder/'questions.md').read_text() for x in q))
result={'status':'MECHANICAL_CHECKS_PASSED_CONTENT_AUDIT_PENDING','questions':len(q),'by_field':dict(collections.Counter(x['field'] for x in q)),'checks':checks,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir()) if p.is_file()}}
(root/'reports/social_v1_verification_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
