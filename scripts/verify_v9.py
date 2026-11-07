"""Read-only, independent parsing/diff verification. Optional output is external to tracked data."""
import argparse,collections,csv,hashlib,json,re,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'data/v9'
def load(p):return json.loads(p.read_text())
def rows(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
 a=load(R/'data/v8/questions.json');b=load(F/'questions.json');checks=[]
 def ck(n,c):
  assert c,n
  checks.append({'name':n,'status':'PASS'})
 ck('1040 unique IDs and unchanged order',len(b)==len({q['id'] for q in b})==1040 and [q['id'] for q in a]==[q['id'] for q in b])
 back=[{k:json.loads(v) for k,v in x.items() if v!=''} for x in rows(F/'questions.csv')];ck('JSON/CSV full-field types match',back==b)
 ck('3 distinct choices and valid answer',all(len(q['choices'])==len(set(q['choices']))==3 and type(q['correct_index']) is int and 0<=q['correct_index']<3 and q['correct_answer']==q['choices'][q['correct_index']] for q in b))
 defs=load(F/'canonical_definitions.json');names={v:k for k,v in defs.items()};ck('501 unique canonical definitions',len(defs)==len(names)==501)
 ck('500 meaning 500 context 40 reading',collections.Counter(q['question_type'] for q in b)=={'meaning':500,'context':500,'logical_reading':40})
 for q in b:
  if q['question_type']=='meaning':
   ck(q['id']+' all definitions and word names',q['correct_answer']==defs[q['target_word']] and all(d in names and d in q['explanation'] and f'「{names[d]}」' in q['explanation'] for d in q['choices']))
  elif q['question_type']=='context':ck(q['id']+' exact linked definitions',all(f'「{w}」は{defs[w]}' in q['explanation'] for w in q['choices']))
 expected={(y['id'],k):[x.get(k),y.get(k)] for x,y in zip(a,b) for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
 log=rows(F/'change_map_v8_v9.csv');actual={(x['id'],x['field']):[json.loads(x['before']),json.loads(x['after'])] for x in log}
 ck('change map exact before/after and no duplicate rows',expected==actual and len(log)==len(actual))
 olddefs=load(R/'data/v8/canonical_definitions.json');changed={w for w in defs if defs[w]!=olddefs[w]};ck('Exactly four named definition updates',changed=={'虚偽','詭弁','続報','誤報'})
 ck('definition CSV values match',len(rows(F/'definition_changes.csv'))==4 and all(x['before']==olddefs[x['word']] and x['after']==defs[x['word']] for x in rows(F/'definition_changes.csv')))
 oldnames={v:k for k,v in olddefs.items()};expected_replacements=[]
 for x,y in zip(a,b):
  if x['question_type'] not in ['meaning','context']:continue
  before_words=[oldnames[d] for d in x['choices']] if x['question_type']=='meaning' else x['choices']
  after_words=[names[d] for d in y['choices']] if y['question_type']=='meaning' else y['choices']
  for i,(before_word,after_word) in enumerate(zip(before_words,after_words)):
   if before_word!=after_word:expected_replacements.append((y['id'],i+1,before_word,after_word))
 logged=[(r['id'],int(r['choice_number']),r['before_word'],r['after_word']) for r in rows(F/'distractor_replacements.csv')]
 ck('all six distractor replacements independently reconstructed',len(expected_replacements)==6 and logged==expected_replacements)
 quote_count=0
 for q in b:
  if q['question_type']!='logical_reading':continue
  stack=[]
  for i,ch in enumerate(q['explanation']):
   if ch=='「':stack.append(i)
   elif ch=='」':
    assert stack,q['id']
    start=stack.pop();quote_count+=1;assert q['explanation'][start+1:i] in q['passage'],q['id']
  assert not stack,q['id']
 ck('reading quotations remain verbatim',quote_count==40)
 byid={q['id']:q for q in b};ck('requested noun distractors preserve answer indices',byid['JVQ-111-01-M']['choices']==[defs[w] for w in ['事実','虚偽','出典']] and byid['JVQ-113-04-M']['choices']==[defs[w] for w in ['論拠','前提','詭弁']])
 ck('protected question content unchanged',all(x.get(k)==y.get(k) for x,y in zip(a,b) for k in ['id','grade','prompt','passage','correct_index','review_status','claude_audit','release_status','furigana_policy']))
 content_ids={id for id,k in expected if k!='grade_policy'};ck('audit packet exact content-changed IDs',sorted(content_ids)==load(F/'audit_focus.json')['producer_content_revised_ids'])
 for x,y in zip(a,b):
  if x['question_type']=='context':
   ck(x['id']+' scene and rationale prefix preserved',x['explanation'].split(f'「{x["target_word"]}」は')[0]==y['explanation'].split(f'「{x["target_word"]}」は')[0])
 ck('all policies retain no furigana, 2025 edition pending tables',all(q['furigana_policy']=='none_by_user_request_20261105' and q['grade_policy']=='mitsumura_r7_2025_grade_and_kanji_tables_pending' and '<ruby' not in q['prompt']+q['explanation'] for q in b))
 result={'status':'MECHANICAL_PASS_INDEPENDENT_CONTENT_AUDIT_PENDING','questions':len(b),'changed_fields':len(log),'changed_ids':len({x[0] for x in expected}),'content_changed_ids':sorted(content_ids),'content_changed_fields':sum(k!='grade_policy' for id,k in expected),'checks':checks,'content_changed_by_type':dict(collections.Counter(byid[id]['question_type'] for id in content_ids)),'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in F.iterdir() if p.is_file()},'textbook_all_word_grade_kanji_alignment':'pending actual grade-end lists/indexes'}
 out=args.output or Path(tempfile.mkdtemp(prefix='manabi-v9-'))/'result.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','sha256','content_changed_ids']}|{'check_count':len(checks),'output':str(out)},ensure_ascii=False))
if __name__=='__main__':main()
