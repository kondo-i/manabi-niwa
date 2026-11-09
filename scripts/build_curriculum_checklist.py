"""Producer-authored curriculum work list, not a verbatim or exhaustive official syllabus."""
import csv,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];qs=json.loads((R/'data/expansion/v1/questions.json').read_text());rows=[]
M={1:'signed:正負の数,expressions:文字式,linear-equation:一次方程式,proportion:比例・反比例,plane-geometry:平面図形,solid-geometry:空間図形,data:データの活用',2:'polynomials:式の計算,simultaneous:連立方程式,linear-function:一次関数,parallel-angles:平行線と角,triangle-properties:図形の性質と合同,probability:確率,boxplot:四分位範囲と箱ひげ図',3:'factorization:展開・因数分解,square-roots:平方根,quadratic-equation:二次方程式,quadratic-function:関数y=ax²,similarity:相似,circle:円周角,pythagoras:三平方の定理,sampling:標本調査'}
Sc={1:'classification:生物の分類,flower:植物のつくり,animals:動物の分類,matter:物質の性質,gas:気体,state:状態変化,density:密度,concentration:水溶液,solubility:溶解度と再結晶,light:光,sound:音,force:力,spring:ばね,volcano:火山,earthquake:地震,strata:地層,observation:観察・条件制御',2:'photosynthesis:光合成,transpiration:蒸散,digestion:消化,circulation:循環,nervous:神経,atoms:原子・分子,oxidation:酸化・還元,chemical-mass:化学変化と質量,current:電流と抵抗,power:電力,magnetism:電流と磁界,humidity:湿度,weather:気象観測,fronts:前線,cloud:雲',3:'division:細胞分裂,reproduction:生殖,inheritance:遺伝,evolution:進化,ecosystem:生態系,acid:酸とアルカリ,neutralization:中和,battery:電池,ions:イオン,motion:運動,work:仕事,energy:エネルギー,celestial:日周運動,seasons:季節,astronomy:天体の動き,environment:自然と人間'}
E={1:'past:過去形,can:can,there:存在文,future:未来の表現,be:be動詞,present:一般動詞現在,questions:疑問詞,progressive:現在進行形,imperative:命令文,pronouns:代名詞,reading:読解,listening:聞くこと,speaking:話すこと,writing:書くこと',2:'infinitive:不定詞,gerund:動名詞,comparison:比較,must:助動詞,conjunction:接続詞,past-progressive:過去進行形,passive:受け身,reading:読解,listening:聞くこと,speaking:話すこと,writing:書くこと',3:'relative:関係代名詞,participle:分詞,indirect:間接疑問,perfect-progressive:現在完了進行形,wish:仮定法,present-perfect:現在完了,reading:読解,listening:聞くこと,speaking:話すこと,writing:書くこと'}
J='word-classes:文法・品詞,sentence:文の構造,vocabulary:語彙,expository:説明的文章,literature:文学的文章,poetry:詩歌・表現,classics:古典,writing:書くこと,speaking:話す・聞く,information:情報の扱い,kanji:漢字の読み書き'
S={1:'coordinates:位置,map:地図,asia:アジア,europe:ヨーロッパ,africa:アフリカ,north-america:北アメリカ,south-america:南アメリカ,oceania:オセアニア,climate:世界の気候,inquiry:地域調査,early-history:古代までの歴史',2:'ancient:古代,medieval:中世,early-modern:近世,meiji:近代日本,industrial:産業革命,sources:史料,chronology:年表,japan-climate:日本の自然,japan-industry:日本の産業,japan-inquiry:日本の地域調査,japan-regions:日本の諸地域,world-wars:世界大戦,postwar:戦後の歴史',3:'rights:人権,diet:国会,cabinet:内閣,courts:司法,local:地方自治,market:市場,labor:労働,finance:財政,international:国際社会,sustainability:持続可能性,constitution:憲法原理,money:金融,social-security:社会保障,modern-society:現代社会'}
for subject,table in [('math',M),('science',Sc),('english',E),('japanese',{g:J for g in [1,2,3]}),('social',S)]:
 for grade,topics in table.items():
  for pair in topics.split(','):
   key,title=pair.split(':');matches=[]
   for q in qs:
    if (q['subject'],q['grade'])!=(subject,grade):continue
    topic=q.get('curriculumTopic',q['unitId'].split('-',3)[-1])
    if topic==key:matches.append(q)
   rows.append({'subject':subject,'draft_grade':grade,'topic_key':key,'topic_title':title,'new_instances':len(matches),'new_families':len({q['family'] for q in matches}),'coverage_status':'PARTIAL_SEED_NOT_UNIT_COMPLETE' if matches else 'NO_NEW_SEED_EXISTING_BANK_UNMAPPED','release_status':'BLOCKED_PENDING_REVIEW','remaining_work':'小単元の細分化・複数形式・基礎標準応用・誤答排他性・学年妥当性・既存教材との意味重複確認','grade_basis':'制作仮配当。特に英語文法・社会は学習指導要領の固定学年配当ではない','source':'https://www.mext.go.jp/a_menu/shotou/new-cs/1387016.htm'})
F=R/'reports/release_prep/v1';F.mkdir(parents=True,exist_ok=True)
with (F/'curriculum_checklist.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(F/'curriculum_checklist_summary.json').write_text(json.dumps({'status':'INITIAL_PRODUCER_WORK_BREAKDOWN_NOT_EXHAUSTIVE_OFFICIAL_UNIT_CERTIFICATION','rows':len(rows),'partial_seed_rows':sum(r['new_instances']>0 for r in rows),'no_new_seed_rows':sum(r['new_instances']==0 for r in rows),'existing900':'not mapped to every objective; zero new seed does not imply zero existing questions','source_fetch':'MEXT math/science/japanese PDFs obtained; math/science text inspected; English/social full mapping still pending'},ensure_ascii=False,indent=2)+'\n')
print(len(rows),'rows; missing new seeds',sum(r['new_instances']==0 for r in rows))
