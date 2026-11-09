import argparse,csv,json,re,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();F=R/'data/social/v5';a=json.loads((R/'data/social/v4/questions.json').read_text());b=json.loads((F/'questions.json').read_text())
 with (F/'questions.csv').open(newline='') as f:back=[{k:json.loads(v) for k,v in q.items() if v!=''} for q in csv.DictReader(f)]
 assert back==b and len(b)==32 and len({q['id'] for q in b})==32
 assert all(len(q['choices'])==len(set(q['choices']))==3 and q['choices'][q['correct_index']]==q['correct_answer'] for q in b)
 diff={(y['id'],k):(x[k],y[k]) for x,y in zip(a,b) for k in y if x[k]!=y[k]}
 with (F/'change_map_v4_v5.csv').open(newline='') as f:rows=list(csv.DictReader(f))
 assert len(rows)==len(diff)==1 and {(r['id'],r['field']):(json.loads(r['before']),json.loads(r['after'])) for r in rows}==diff
 q=next(q for q in b if q['id']=='SOC-HIS-011');assert not re.search(r'\d{3,4}年',q['explanation']) and q['correct_answer']=='学制'
 assert len(json.loads((R/'reports/app_review/v4/questions.json').read_text()))==188
 out=args.output or Path(tempfile.mkdtemp(prefix='social-v5-'))/'result.json';out.parent.mkdir(parents=True,exist_ok=True);result={'status':'MECHANICAL_PASS_CONTENT_AUDIT_PENDING','social':32,'content_changed':1,'changed_fields':1,'app_questions_unchanged':188,'year_in_HIS011_explanation':False};out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)
if __name__=='__main__':main()
