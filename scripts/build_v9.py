"""Round-8 requested definition corrections and all linked uses; never edit prior drafts."""
import copy,csv,json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from build_v8 import write_json,write_csv,encode
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/v9'
old=json.loads((ROOT/'data/v8/questions.json').read_text());data=copy.deepcopy(old)
olddefs=json.loads((ROOT/'data/v8/canonical_definitions.json').read_text());defs=olddefs|{
 '虚偽':'事実と異なるうその内容を指すこと',
 '詭弁':'見かけは筋が通るようでも不正確な議論を指すこと',
 '続報':'前に伝えた出来事のその後を知らせる報道を指すこと',
 '誤報':'実際と違う内容を伝えてしまった報道を指すこと'}
name={v:k for k,v in olddefs.items()};replacements=[]
replace={'JVQ-111-01-M':['事実','虚偽','出典'],'JVQ-113-04-M':['論拠','前提','詭弁']}
for before,q in zip(old,data):
 q['grade_policy']='mitsumura_r7_2025_grade_and_kanji_tables_pending'
 if q['question_type']=='meaning':
  prev=[name[d] for d in before['choices']];words=replace.get(q['id'],prev)
  for i,(a,b) in enumerate(zip(prev,words)):
   if a!=b:replacements.append({'id':q['id'],'choice_number':i+1,'before_word':a,'after_word':b,'reason':'Claude_round8_requested_noncompeting_noun_distractor'})
  q['choices']=[defs[w] for w in words];q['correct_answer']=defs[q['target_word']]
  if q['choices']!=before['choices']:
   wrong=[w for i,w in enumerate(words) if i!=q['correct_index']]
   q['explanation']=f'「{q["target_word"]}」は{q["correct_answer"]}。一方、「{wrong[0]}」は{defs[wrong[0]]}。また、「{wrong[1]}」は{defs[wrong[1]]}。それぞれの意味の中心を比べて区別しよう。'
 elif q['question_type']=='context':
  for w in q['choices']:q['explanation']=q['explanation'].replace(f'「{w}」は{olddefs[w]}',f'「{w}」は{defs[w]}')
  # Linked rereading found the previously noted exaggeration/false-content overlap.
  if q['id']=='JVQ-111-02-C':
   words=['精査','誇大','訂正']
   for i,(a,b) in enumerate(zip(before['choices'],words)):
    if a!=b:replacements.append({'id':q['id'],'choice_number':i+1,'before_word':a,'after_word':b,'reason':'producer_linked_review_existing_exaggeration_false_content_overlap'})
   q['choices']=words
   prefix=before['explanation'].split(f'「{q["target_word"]}」は')[0]
   q['explanation']=prefix+f'「誇大」は{defs["誇大"]}。「精査」は{defs["精査"]}、「訂正」は{defs["訂正"]}。この場面では調べ直したり誤りを直したりせず、小さな効果を実際以上に大きく見せている。'

write_json(OUT/'questions.json',data);fields=list(dict.fromkeys(k for q in data for k in q))
write_csv(OUT/'questions.csv',[{k:encode(q[k]) if k in q else '' for k in fields} for q in data],fields)
changes=[{'id':q['id'],'field':k,'before':encode(before[k]),'after':encode(q[k]),'reason':'user_confirmed_2025_edition' if k=='grade_policy' else 'round8_definition_distractor_and_linked_explanation'} for before,q in zip(old,data) for k in q if before[k]!=q[k]]
write_csv(OUT/'change_map_v8_v9.csv',changes);write_json(OUT/'canonical_definitions.json',defs)
write_csv(OUT/'definition_changes.csv',[{'word':w,'before':olddefs[w],'after':defs[w]} for w in defs if defs[w]!=olddefs[w]])
write_csv(OUT/'distractor_replacements.csv',replacements)
ids={r['id'] for r in changes if r['field']!='grade_policy'}
write_json(OUT/'audit_focus.json',{'producer_content_revised_ids':sorted(ids),'questions':[q for q in data if q['id'] in ids],'semantic_reason':{'虚偽':'うその内容という名詞の指示対象を保持。事実と出典はうその内容ではない。','詭弁':'議論そのものを定義し、すり替えという手法を意味問題の誤答から除く。論拠は根拠、前提は推論前の条件。','続報':'既報の出来事のその後を知らせる報道。拡散は情報が広がること、誤報は実際と異なる報道。','誤報':'報道を指す名詞の定義に戻し、全使用箇所で一致させる。'},'independent_review':'pending; producer rationale is not independent approval'})
write_json(OUT/'textbook_policy.json',{'confirmed_on':'2026-11-07','japanese_publisher':'光村図書','edition':'令和7年度版（2025年度）','edition_evidence':'user_answer_in_current_session','furigana':'none','grades':'existing 1-3 assignments unchanged','grade_end_kanji_lists':'not_provided','indexes':'not_provided','all_500_words_listed_in_textbook':'not_verified','alignment_status':'edition_confirmed_grade_tables_and_index_comparison_pending'})
print(json.dumps({'questions':len(data),'fields':len(changes),'content_ids':len(ids),'definition_changes':4,'distractor_choices':len(replacements)},ensure_ascii=False))
