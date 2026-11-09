import copy,csv,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'data/social/v5';F.mkdir(parents=True,exist_ok=True)
a=json.loads((R/'data/social/v4/questions.json').read_text());b=copy.deepcopy(a)
q=next(q for q in b if q['id']=='SOC-HIS-011');q['explanation']=q['explanation'].replace('1872年の学制','学制')
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
dump(F/'questions.json',b)
keys=list(dict.fromkeys(k for q in b for k in q))
with (F/'questions.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:json.dumps(q[k],ensure_ascii=False) if k in q else '' for k in keys} for q in b)
changes=[{'id':y['id'],'field':k,'before':json.dumps(x[k],ensure_ascii=False),'after':json.dumps(y[k],ensure_ascii=False),'reason':'round9_remove_answer_year_of_another_question'} for x,y in zip(a,b) for k in y if x[k]!=y[k]]
with (F/'change_map_v4_v5.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
for name in ['sources.json','textbook_policy.json']:
 if (R/'data/social/v4'/name).exists():shutil.copyfile(R/'data/social/v4'/name,F/name)
dump(F/'audit_focus.json',{'changed_question':q,'scope':'one explanation; other31 social and188 app items unchanged'})
(F/'questions.md').write_text('\n\n'.join(q['id']+'\n'+q['prompt']+'\n'+q['explanation'] for q in b)+'\n')
