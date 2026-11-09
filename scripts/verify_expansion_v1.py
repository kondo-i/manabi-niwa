"""Independent symbolic solver plus structural checks. Seed semantics are separately pending."""
import argparse,csv,json,statistics,tempfile,collections
from pathlib import Path
import sympy as s
R=Path(__file__).resolve().parents[1];F=R/'data/expansion/v1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();qs=json.loads((F/'questions.json').read_text());counts=collections.Counter();numerical=0;manual=0
 with (F/'questions.csv').open(newline='') as f:back=[{k:json.loads(v) for k,v in r.items() if v!=''} for r in csv.DictReader(f)]
 assert qs==back and len(qs)==len({q['id'] for q in qs})==len({q['prompt'] for q in qs})
 for q in qs:
  counts[(q['subject'],q['grade'])]+=1;o=q['oracle'];kind=o['kind'];ans=q['answer']
  if kind=='authored_choice':assert q['choices'][ans] and len(q['choices'])==len(set(q['choices']))==3 and ans==o['expected_answer'];manual+=1;continue
  if kind=='equivalent_choices':
   matches=[i for i,v in enumerate(o['choices']) if s.simplify(s.sympify(v)-s.sympify(o['target']))==0];assert matches==[ans],q['id'];numerical+=1;continue
  if kind=='expression':expected=float(s.sympify(o['expression']))
  elif kind=='equation':
   vals=[float(v) for v in s.solve(s.sympify(o['expression']),s.Symbol(o['variable'])) if v.is_real];expected=max(vals) if o['select']=='max' else vals[0];assert o['select']=='max' or len(vals)==1
  elif kind=='system':expected=float(s.solve([s.sympify(v) for v in o['equations']],[s.Symbol('x'),s.Symbol('y')])[s.Symbol(o['variable'])])
  elif kind=='median':expected=statistics.median(o['values'])
  elif kind=='probability':expected=float(s.Rational(o['favorable'],o['total']))
  elif kind=='positive_root':expected=float(s.sqrt(o['square']))
  elif kind=='hypotenuse':expected=float(s.sqrt(sum(v*v for v in o['legs'])))
  elif kind=='equal':expected=o['given']
  else:raise ValueError(kind)
  assert abs(expected-ans)<1e-8,(q['id'],expected,ans);numerical+=1
 assert len(counts)==15,counts
 out=a.output or Path(tempfile.mkdtemp(prefix='manabi-expansion-'))/'results.json';out.parent.mkdir(parents=True,exist_ok=True);result={'status':'STRUCTURE_AND_ORACLE_PASS_NOT_RELEASE_APPROVED','instances':len(qs),'numerical_or_symbolic_checks':numerical,'authored_choice_structure_only':manual,'by_subject_grade':{f'{k[0]}_g{k[1]}':v for k,v in sorted(counts.items())},'unique_families':len({q['family'] for q in qs}),'semantic_review':'not a complete independent approval; publisher vocabulary and curriculum granularity not fully checked','all_subject_grade_cells_nonempty':True};out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
