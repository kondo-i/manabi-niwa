"""Rebuild a word-character crosswalk from a pinned third-party reference snapshot."""
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'data/kanji_reference/20261109';ref=json.loads((F/'third_party_character_reference.json').read_text())['character_reference_grades'];qs=json.loads((R/'data/v10/questions.json').read_text());rows=[]
for q in qs:
 if q['question_type']!='meaning':continue
 cs=list(dict.fromkeys(c for c in q['target_word'] if re.match(r'[\u3400-\u9fff]',c)));rows.append({'lexeme_id':q['lexeme_id'],'word':q['target_word'],'current_app_grade':q['grade'],'character_reference':json.dumps({c:ref.get(c,[]) for c in cs},ensure_ascii=False),'not_in_reference':' '.join(c for c in cs if c not in ref),'judgment':'NOT_A_WORD_GRADE_DETERMINATION'})
assert len(rows)==500
with (F/'v10_500_words_character_crosswalk.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
