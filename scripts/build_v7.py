"""Round 6 production revision. Candidates below are producer selections, NOT Claude CSV."""
import csv, json, pathlib, copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
def write_json(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_csv(p,rows,fields=None):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def j(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def differences(old,new):
 return [{'id':b['id'],'field':k,'before':j(a[k]),'after':j(b[k]),'reason':'第6回監査対応：同型の誤答への差し替え、定義の連動修正、解説の更新'} for a,b in zip(old,new) for k in a if a[k]!=b[k]]
def export_questions(folder,qs):
 write_json(folder/'questions.json',qs)
 # Explicit JSON encoding preserves optional fields and nested values without loss.
 fields=list(dict.fromkeys(k for q in qs for k in q))
 write_csv(folder/'questions.csv',[{k:j(q[k]) if k in q else '' for k in fields} for q in qs],fields)
def main():
 old=json.loads((ROOT/'data/v6/questions.json').read_text(encoding='utf-8'));new=copy.deepcopy(old)
 m=[q for q in old if q['question_type']=='meaning']
 olddefs={q['target_word']:q['correct_answer'] for q in m}
 olddefs['霧']='細かな水滴が空気中に浮かんで、視界が白くかすむこと'
 names={d:w for w,d in olddefs.items()};defs=olddefs.copy()
 defs.update({'国際':'国と国との間で行われること','正確性':'誤りがなく確かな性質であること','透明性':'判断の過程や情報が外から分かる性質であること'})
 # Each row names the ONE odd distractor's replacement; all three definitions
 # are independently checked in verify_v7.py. No nearest-neighbour selection.
 selected='''003-01 証拠
003-02 事実
003-03 観察
011-01 動揺
011-02 疑念
011-03 歓喜
011-04 感謝
012-01 期待
012-03 安堵
012-04 落胆
013-01 非難
013-02 不安
013-04 感謝
015-02 軽蔑
015-03 傲慢
015-04 信条
017-01 興奮
017-02 放心
017-03 疑念
019-02 慎重
019-03 厳格
019-04 価値観
033-01 比喩
033-03 説明文
033-04 論説文
038-01 比較
038-03 同音異義語
038-04 類義語
039-01 共通点
039-02 相違点
039-03 列挙
039-04 要約
040-02 再読
040-03 要約
040-04 証拠
042-01 前提
042-03 調査
042-04 改善
043-01 結果
043-02 共通点
043-03 集計
043-04 分類
044-01 類推
044-02 意見
044-04 公平
047-02 撤回
047-03 提案
047-04 仮説
052-01 法律
052-02 奉仕
052-04 責務
053-01 奉仕
053-02 責務
053-03 法律
053-04 寄付
055-01 目標
055-03 供給
055-04 消費
058-02 遵守
058-03 自主
058-04 慣習
059-01 秩序
059-02 法律
059-03 移住
059-04 選挙
060-01 紛争
060-02 事件
060-03 避難
061-03 直後
061-04 中断
063-01 契機
063-03 再開
063-04 中断
081-01 曇天
081-02 薄明
081-03 夜明け
082-01 閑散
082-02 閑散
082-03 暗闇
084-03 豪雨
085-01 日差し
085-02 暗闇
085-03 逆光
085-04 芽吹き
090-01 鮮明
090-02 ぎこちない
090-03 正確性
090-04 再現性
091-01 冷静
091-02 疲弊
091-03 不安
095-01 日差し
095-03 紅葉
095-04 落葉
105-01 当面
105-03 試行錯誤
105-04 優柔不断
108-01 疑念
108-03 優柔不断
108-04 前途多難
111-01 仮説
111-03 誇張
113-02 誇張
113-03 隠蔽
113-04 仮説
114-02 伝達
114-03 訂正
114-04 原因
119-01 方針
119-02 改善
119-03 予定
119-04 持続的
124-01 黙認
124-02 明示
124-03 論点
124-04 出典'''
 swaps=dict(line.split() for line in selected.splitlines())
 # 逆光 is an illumination direction; 夜明け is the onset of morning.
 swaps['081-03']='夜明け'
 log=[]
 original_mixed=[]
 for q in new:
  if q['question_type']=='meaning':
   ws=[names[d] for d in q['choices']]
   types=[d.endswith('であること') for d in q['choices']]
   key=q['id'][4:-2]
   if len(set(types))>1:
    original_mixed.append(q['id'])
    odd=next(i for i,t in enumerate(types) if types.count(t)==1)
    assert odd!=q['correct_index']
    if key in swaps:
     before=ws[odd];ws[odd]=swaps[key]
     log.append({'id':q['id'],'choice_number':odd+1,'before_word':before,'after_word':ws[odd],
      'target_word':q['target_word'],'target_definition':defs[q['target_word']], 'replacement_definition':defs[ws[odd]],
      'semantic_review':'制作側で意味を比較して採用。正答は「'+defs[q['target_word']]+'」、誤答は「'+defs[ws[odd]]+'」。独立した意味競合の再監査を要請。',
      'provenance':'producer_selected_without_Claude_CSV'})
    else:assert key in ['078-01','078-02','078-03','078-04']
   if key=='061-04':
    i=ws.index('維持');ws[i]='進展'
    log.append({'id':q['id'],'choice_number':i+1,'before_word':'維持','after_word':'進展','target_word':q['target_word'],'target_definition':defs[q['target_word']],'replacement_definition':defs['進展'],'semantic_review':'長く変わらず続くことと、新しい段階へ進むことを区別。','provenance':'user_supplied_round6_text'})
   q['choices']=[defs[w] for w in ws];q['correct_answer']=q['choices'][q['correct_index']]
   if q['choices']!=next(x for x in old if x['id']==q['id'])['choices']:
    wrong=[w for i,w in enumerate(ws) if i!=q['correct_index']]
    q['explanation']=f'「{q["target_word"]}」は{defs[q["target_word"]]}。一方、「{wrong[0]}」は{defs[wrong[0]]}。また、「{wrong[1]}」は{defs[wrong[1]]}。それぞれの意味の中心を比べて区別しよう。'
  elif q['question_type']=='context':
   for w,d in olddefs.items():
    if defs[w]!=d:q['explanation']=q['explanation'].replace(f'「{w}」は{d}',f'「{w}」は{defs[w]}')
 assert len(original_mixed)==120
 folder=ROOT/'data/v7';export_questions(folder,new)
 write_csv(folder/'change_map_v6_v7.csv',differences(old,new))
 write_csv(folder/'distractor_replacements.csv',log)
 write_csv(folder/'definition_changes.csv',[{'word':w,'before':olddefs[w],'after':d} for w,d in defs.items() if olddefs[w]!=d])
 write_json(folder/'canonical_definitions.json',defs)
 print(json.dumps({'original_mixed':len(original_mixed),'replacement_choices':len(log),'changed_questions':len({d['id'] for d in differences(old,new)}),'changed_fields':len(differences(old,new))}))
if __name__=='__main__':main()
