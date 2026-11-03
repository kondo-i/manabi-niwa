"""Apply round 6 social edits and produce lossless draft exports."""
import csv,json,pathlib,copy
R=pathlib.Path(__file__).resolve().parents[1];D=R/'data/social/v2';D.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(p,rows):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def js(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
old=load('data/social/v1/questions.json');qs=copy.deepcopy(old);by={q['id']:q for q in qs}
def update(id,prompt,choices,answer,reason,wrong,sources=None):
 q=by['SOC-'+id]
 if prompt:q['prompt']=prompt
 q.update(choices=choices,correct_answer=answer,correct_index=choices.index(answer),explanation=reason,
  distractor_notes=[{'choice':c,'reason':r} for c,r in wrong.items()])
 if sources:q['source_ids']=sources
update('GEO-010','同じ大きさの紙に地図をかくとき、5万分の1の地図と比べて2万5千分の1の地図にあてはまる説明はどれか。',
 ['狭い範囲を、より大きく表せる','広い範囲を、より小さく表せる','表す範囲も物の大きさも変わらない'],'狭い範囲を、より大きく表せる',
 '地図の1cmは5万分の1なら500m、2万5千分の1なら250m。同じ紙なら2万5千分の1のほうが狭い範囲を大きく示せる。',
 {'広い範囲を、より小さく表せる':'それは5万分の1の地図のほうの特徴。','表す範囲も物の大きさも変わらない':'縮尺を変えると、同じ紙に収まる実際の範囲と地図上の物の大きさが変わる。'})
update('HIS-003',None,['原則として米で納める','原則として労働で納める','原則としてお金で納める'],'原則としてお金で納める',
 '地租改正では、地価をもとに税額を決め、土地にかかる税をお金で納めるようにした。',
 {'原則として米で納める':'従来の物納から金納へと改められた。','原則として労働で納める':'労働で納める仕組みに改めたのではない。'})
update('HIS-010','大日本帝国憲法のもとで、主権を持つとされたのは誰か。',['天皇','国民','帝国議会'],'天皇',
 '大日本帝国憲法では天皇が主権者とされた。日本国憲法では主権が国民に移った。',
 {'国民':'国民主権は日本国憲法の基本原則。','帝国議会':'帝国議会には法律案などを審議する役割があったが、主権者ではない。'},['MEIJI_TEXT','MEIJI_CONST','CONST'])
update('CIV-006',None,['職業や収入を全員同じにそろえる','意見の違いによって扱いに差をつける','社会的身分などによって差別されない'],'社会的身分などによって差別されない',
 '日本国憲法第14条は、社会的身分や信条などを理由に差別されないことを定めている。',
 {'職業や収入を全員同じにそろえる':'職業や収入を同じにすることは、法の下の平等の意味ではない。','意見の違いによって扱いに差をつける':'信条などを理由とする差別を認める規定ではない。'})
update('CIV-008',None,['希望する品物を無料で受け取れる','働かなくても同じ収入が保障される','健康で文化的な最低限度の生活を営む'],'健康で文化的な最低限度の生活を営む',
 '日本国憲法第25条は、人が健康で文化的な最低限度の生活を営む権利を保障する。',
 {'希望する品物を無料で受け取れる':'希望する品を無料で手に入れる権利を定めた条文ではない。','働かなくても同じ収入が保障される':'人の収入を同じ金額にする規定ではない。'})
update('CIV-009',None,['子どもが学校を設置する義務','子どもが教科書を編集する義務','保護者が、保護する子どもに普通教育を受けさせる義務'],'保護者が、保護する子どもに普通教育を受けさせる義務',
 '日本国憲法第26条第2項の義務は、子ども本人ではなく、子どもを保護する人が負う。',
 {'子どもが学校を設置する義務':'子どもに学校の設置を求める条文ではない。','子どもが教科書を編集する義務':'子どもに教科書の編集を求める条文ではない。'})
update('CIV-010',None,['法律に従って税を納める','年齢に関係なく全員が同額を納める','国会議員は税を納めなくてよい'],'法律に従って税を納める',
 '日本国憲法第30条は、法律の定めに従って国民が納税の義務を負うことを示している。',
 {'年齢に関係なく全員が同額を納める':'納める条件や金額は税の法律による。同額を課す規定ではない。','国会議員は税を納めなくてよい':'議員であることを理由に納税義務を免除する規定ではない。'})
# Cite the pages that actually state each historical fact.
by['SOC-HIS-006']['source_ids']=['MEIJI_CONST']
by['SOC-HIS-007']['source_ids']=['CONST']
by['SOC-HIS-008']['source_ids']=['CONST']
# Fixed audited order, independent of any deployed application shuffle.
orders={'geography':[1,0,2,2,0,1,2,0,1,0],'history':[2,1,0,1,2,0,0,2,1,1],'civics':[2,0,1,0,2,1,2,2,0,1]}
amended={'SOC-'+x for x in ['GEO-010','HIS-003','HIS-010','CIV-006','CIV-008','CIV-009','CIV-010']}
for q in qs:
 pos=orders[q['field']][int(q['id'][-3:])-1];a=q['correct_answer'];wrong=[c for c in q['choices'] if c!=a];wrong.insert(pos,a);q['choices']=wrong;q['correct_index']=pos
 notes={d['choice']:d for d in q['distractor_notes']};q['distractor_notes']=[notes[c] for c in q['choices'] if c!=a]
 if q['id'] in amended:q['explanation']+=' 誤答の確認：'+' '.join(f'「{d["choice"]}」：{d["reason"]}' for d in q['distractor_notes'])
sources=load('data/social/v1/sources.json');sources['checked_date_jst']='2026-11-03';sources['source_access']='制作側が参照先の本文を取得して確認。参照箇所と照合範囲は報告書参照。'
sources['sources']['TIMELINE']['basis']='1871年廃藩置県、1872年学制、1873年地租改正を年表本文で確認。'
sources['sources']['MEIJI_CONST']={'title':'国立公文書館 大日本帝国憲法が発布される','url':'https://www.archives.go.jp/ayumi/kobetsu/m22_1889_01.html','basis':'1889年2月11日の発布、天皇が統治権を総攬、帝国議会は法律案・予算案の審議権。解説本文を確認。'}
sources['sources']['MEIJI_TEXT']={'title':'国立国会図書館 大日本帝国憲法','url':'https://www.ndl.go.jp/constitution/etc/j02.html','basis':'第1条・第4条の統治権、第5条・第37条・第38条の帝国議会の協賛・議決。条文本文を確認。'}
dump(D/'questions.json',qs);dump(D/'sources.json',sources)
csvout(D/'questions.csv',[{k:js(v) if isinstance(v,list) else v for k,v in q.items()} for q in qs])
diff=[{'id':b['id'],'field':k,'before':js(a[k]),'after':js(b[k])} for a,b in zip(old,qs) for k in a if a[k]!=b[k]]
csvout(D/'change_map_social_v1_v2.csv',diff)
lines=['# 社会第2稿：地理・明治・憲法（試作30問）','', '社会全体の網羅教材ではありません。配信・独立再監査は未実施。','']
for q in qs:
 lines.extend([f'## {q["id"]}',q['prompt'],'',*[f'{i}. {c}' for i,c in enumerate(q['choices'],1)],'',f'正答：{q["correct_index"]+1}. {q["correct_answer"]}',q['explanation'],'出典：'+'、'.join(f'[{sources["sources"][s]["title"]}]({sources["sources"][s]["url"]})' for s in q['source_ids']),''])
(D/'questions.md').write_text('\n'.join(lines),encoding='utf-8')
