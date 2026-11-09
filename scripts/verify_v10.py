import argparse,csv,json,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();a=json.loads((R/'data/v9/questions.json').read_text());F=R/'data/v10';b=json.loads((F/'questions.json').read_text());defs=json.loads((F/'canonical_definitions.json').read_text());names={v:k for k,v in defs.items()};checks=[]
 def ck(name,v):
  assert v,name
  checks.append(name)
 with (F/'questions.csv').open(newline='') as f:back=[{k:json.loads(v) for k,v in r.items() if v!=''} for r in csv.DictReader(f)]
 ck('CSV all fields and types',back==b);ck('1040 IDs/order',len(b)==len({q['id'] for q in b})==1040 and [q['id'] for q in a]==[q['id'] for q in b]);ck('choices/answers',all(len(q['choices'])==len(set(q['choices']))==3 and q['choices'][q['correct_index']]==q['correct_answer'] for q in b))
 for q in b:
  if q['question_type']=='meaning':ck(q['id'],q['correct_answer']==defs[q['target_word']] and all(d in names and d in q['explanation'] and '「'+names[d]+'」' in q['explanation'] for d in q['choices']))
  elif q['question_type']=='context':ck(q['id'],all('「'+w+'」は'+defs[w] in q['explanation'] for w in q['choices']))
 diff={(y['id'],k):(x[k],y[k]) for x,y in zip(a,b) for k in y if x[k]!=y[k]}
 with (F/'change_map_v9_v10.csv').open(newline='') as f:r=list(csv.DictReader(f))
 ck('exact two-field change map',len(r)==len(diff)==2 and {(x['id'],x['field']):(json.loads(x['before']),json.loads(x['after'])) for x in r}==diff and {id for id,k in diff}=={'JVQ-114-03-C'})
 for id in ['JVQ-114-01-M','JVQ-114-01-C','JVQ-114-03-M']:ck(id+' protected',next(q for q in a if q['id']==id)==next(q for q in b if q['id']==id))
 q=next(q for q in b if q['id']=='JVQ-114-03-C');ck('requested choices',q['choices']==['誤報','訂正','拡散'] and q['correct_index']==0)
 result={'status':'MECHANICAL_PASS_CONTENT_AUDIT_PENDING','questions':len(b),'content_changed_ids':['JVQ-114-03-C'],'changed_fields':2,'checks_passed':len(checks)};out=args.output or Path(tempfile.mkdtemp(prefix='manabi-v10-'))/'results.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)
if __name__=='__main__':main()
