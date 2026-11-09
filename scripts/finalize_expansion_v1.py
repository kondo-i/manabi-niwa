import collections,csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'data/expansion/v1';qs=json.loads((F/'questions.json').read_text());families=[]
for family in sorted({q['family'] for q in qs}):
 items=[q for q in qs if q['family']==family];q=items[0];families.append({'family':family,'subject':q['subject'],'draft_grade':q['grade'],'instances':len(items),'unit_ids':sorted({q['unitId'] for q in items}),'status':'pending_content_review','qualification':'Instance count is not distinct skill count. Grade placement is provisional.'})
(F/'families.json').write_text(json.dumps(families,ensure_ascii=False,indent=2)+'\n')
