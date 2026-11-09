"""Bounded authored families. Instance counts are not distinct skills or release approval."""
import csv,json,math,random
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];O=R/'data/expansion/v1';O.mkdir(parents=True,exist_ok=True)
questions=[];families=[]
def number(v):return int(v) if float(v).is_integer() else float(v)
def add(subject,grade,unit,title,family,prompt,answer,explanation,oracle,choices=None,case=0):
 id=f'exp-{subject}-g{grade}-{unit}:q{case+1}'
 q={'id':id,'subject':subject,'grade':grade,'unitId':f'exp-{subject}-g{grade}-{unit}','unitTitle':title,'family':family,'type':'choice' if choices else 'number','prompt':prompt,'answer':answer if choices else number(answer),'explanation':explanation,'status':'prototype','auditStatus':'producer_checks_pending','oracle':oracle}
 if choices:q['choices']=choices
 else:q['tolerance']=1e-8
 questions.append(q)
def math_unit(grade,unit,title,make):
 families.append({'subject':'math','grade':grade,'unit':unit,'title':title,'instances':30,'family_count':1,'qualification':'numerical or symbolic family; does not cover all proofs/applications in chapter'})
 for i in range(30):
  p,a,e,o,*rest=make(i)
  add('math',grade,unit,title,'math-'+unit,p,a,e,o,rest[0] if rest else None,i)
def arithmetic(expr,answer):return {'kind':'expression','expression':expr}
def equation(expr,variable='x',select='single'):return {'kind':'equation','expression':expr,'variable':variable,'select':select}
def polynomial(i):
 a=i%7+1;b=i//7+2;target=f'x**2+{a+b}*x+{a*b}';opts=[f'(x+{a})(x+{b})',f'(x+{a})(x+{b+1})',f'(x+{a+1})(x+{b+1})'];exprs=[f'(x+{a})*(x+{b})',f'(x+{a})*(x+{b+1})',f'(x+{a+1})*(x+{b+1})'];rot=i%3;opts=opts[rot:]+opts[:rot];exprs=exprs[rot:]+exprs[:rot];idx=(-rot)%3
 return f'式 x²＋{a+b}x＋{a*b} を因数分解したものはどれか。',idx,f'積が{a*b}、和が{a+b}になる2数は{a}と{b}なので、(x＋{a})(x＋{b})。',{'kind':'equivalent_choices','target':target,'choices':exprs},opts
math_unit(1,'signed','正の数・負の数',lambda i:(f'({i-18})＋({12-2*i}) を計算しなさい。',-i-6,f'符号を含めて加えると {-i-6}。',arithmetic(f'({i-18})+({12-2*i})',-i-6)))
math_unit(1,'expressions','文字式',lambda i:(f'a＝{i-9} のとき、3a－7 の値を求めなさい。',3*(i-9)-7,f'3×({i-9})－7＝{3*(i-9)-7}。',arithmetic(f'3*({i-9})-7',0)))
math_unit(1,'linear-equation','一次方程式',lambda i:(f'{i%5+2}x＋{i+3}＝{(i%5+2)*(i-10)+i+3} を解きなさい。',i-10,f'両辺から{i+3}を引き、{i%5+2}で割ると x＝{i-10}。',equation(f'{i%5+2}*x+{i+3}-({(i%5+2)*(i-10)+i+3})')))
math_unit(1,'proportion','比例・反比例',lambda i:(f'y は x に反比例する。x＝{i%5+2} のとき y＝{(i+1)*6}。x＝{(i%5+2)*3} のときの y を求めなさい。',(i+1)*2,f'xyの積が一定。xが3倍になるためyは3分の1となり、{(i+1)*2}。',equation(f'{(i%5+2)*3}*x-{(i%5+2)*(i+1)*6}')))
math_unit(1,'plane-geometry','平面図形',lambda i:(f'点A({i-12}, {i%9-4})を y軸について対称移動した点のx座標を求めなさい。',12-i,f'y軸対称ではx座標の符号が反転するため、{12-i}。y座標は変わらない。',arithmetic(f'-({i-12})',0)))
math_unit(1,'solid-geometry','空間図形',lambda i:(f'底面積が{i+3}cm²、高さが{i%7+2}cmの角柱の体積を求めなさい。数値だけ答えなさい（cm³）。',(i+3)*(i%7+2),f'底面積×高さ＝{i+3}×{i%7+2}＝{(i+3)*(i%7+2)}cm³。',arithmetic(f'{i+3}*{i%7+2}',0)))
math_unit(1,'data','データの活用',lambda i:(f'ある測定値は {i+1}、{i+3}、{i+8}、{i+10} だった。この4個のデータの中央値を求めなさい。',i+5.5,f'小さい順の中央2値の平均。({i+3}＋{i+8})÷2＝{i+5.5}。',{'kind':'median','values':[i+1,i+3,i+8,i+10]}))
math_unit(2,'polynomials','式の計算',lambda i:(f'a＝{i-8}、b＝{i%7+1} のとき、2a－3b＋4a＋b の値を求めなさい。',6*(i-8)-2*(i%7+1),f'同類項をまとめると6a－2b。代入すると{6*(i-8)-2*(i%7+1)}。',arithmetic(f'2*({i-8})-3*{i%7+1}+4*({i-8})+{i%7+1}',0)))
math_unit(2,'simultaneous','連立方程式',lambda i:(f'x＋y＝{i+2+i%6}、2x－y＝{2*(i+2)-i%6} のとき、xを求めなさい。',i+2,f'2式を加えると3x＝{3*(i+2)}。したがってx＝{i+2}。',{'kind':'system','equations':[f'x+y-{i+2+i%6}',f'2*x-y-({2*(i+2)-i%6})'],'variable':'x'}))
math_unit(2,'linear-function','一次関数',lambda i:(f'一次関数 y＝{i%5+1}x＋{i-10} で、x＝{i%9-4} のときのyを求めなさい。',(i%5+1)*(i%9-4)+i-10,f'xの値を代入して {(i%5+1)*(i%9-4)+i-10}。',arithmetic(f'{i%5+1}*({i%9-4})+({i-10})',0)))
math_unit(2,'parallel-angles','平行線と角・証明の基礎',lambda i:(f'平行な2直線に1本の直線が交わる。ある角が{i+32}°のとき、その角の同位角は何度か。',i+32,f'平行線の同位角は等しいため、{i+32}°。',{'kind':'equal','given':i+32}))
math_unit(2,'triangle-properties','合同と図形の性質',lambda i:(f'二等辺三角形の頂角が{i+40}°である。一つの底角は何度か。',(140-i)/2,f'底角は等しい。 (180－{i+40})÷2＝{(140-i)/2}°。',equation(f'2*x+{i+40}-180')))
math_unit(2,'probability','確率',lambda i:(f'同じ形の玉が袋に赤{i%5+1}個、白{i//5+2}個入っている。どの玉も同様に確からしく1個取り出す。赤の出る確率を小数で答えなさい。許容誤差0.000001。',(i%5+1)/(i%5+1+i//5+2),f'赤の個数÷全体の個数＝{i%5+1}÷{i%5+1+i//5+2}。',{'kind':'probability','favorable':i%5+1,'total':i%5+1+i//5+2}))
math_unit(2,'boxplot','四分位範囲・箱ひげ図',lambda i:(f'ある集団の第1四分位数が{i+4}、第3四分位数が{2*i+15}。四分位範囲を求めなさい。',i+11,f'第3四分位数－第1四分位数＝{2*i+15}－{i+4}＝{i+11}。',arithmetic(f'{2*i+15}-{i+4}',0)))
math_unit(3,'factorization','多項式の展開・因数分解',polynomial)
math_unit(3,'square-roots','平方根',lambda i:(f'√{(i+2)**2} の値を求めなさい。',i+2,f'√は0以上の平方根を表す。{i+2}²＝{(i+2)**2}なので、{i+2}。',{'kind':'positive_root','square':(i+2)**2}))
math_unit(3,'quadratic-equation','二次方程式',lambda i:(f'(x－{i+2})(x＋{i%6+1})＝0 の大きい方の解を求めなさい。',i+2,f'解は{i+2}と－{i%6+1}。大きい方は{i+2}。',equation(f'(x-{i+2})*(x+{i%6+1})',select='max')))
math_unit(3,'quadratic-function','関数y=ax²',lambda i:(f'y＝{i%4+1}x² について、xが{i%5+1}から{i%5+3}まで増加するときの変化の割合を求めなさい。',(i%4+1)*(2*(i%5+1)+2),f'(yの増加量)÷(xの増加量)から、{(i%4+1)*(2*(i%5+1)+2)}。',arithmetic(f'({i%4+1}*{i%5+3}**2-{i%4+1}*{i%5+1}**2)/2',0)))
math_unit(3,'similarity','相似な図形',lambda i:(f'二つの相似な図形の相似比が小：大＝1：{i%4+2}。小さい図形の面積が{i+3}cm²のとき、大きい図形の面積を求めなさい（cm²）。',(i+3)*(i%4+2)**2,f'面積比は相似比の2乗。{i+3}×{i%4+2}²＝{(i+3)*(i%4+2)**2}cm²。',arithmetic(f'{i+3}*{i%4+2}**2',0)))
math_unit(3,'circle','円周角',lambda i:(f'同じ弧に対する中心角が{2*(i+20)}°。その弧に対する円周角は何度か。',i+20,f'円周角は同じ弧に対する中心角の半分なので、{i+20}°。',equation(f'2*x-{2*(i+20)}')))
math_unit(3,'pythagoras','三平方の定理',lambda i:(f'直角三角形の直角をはさむ2辺が{3*(i+1)}cm、{4*(i+1)}cm。斜辺の長さを求めなさい（cm）。',5*(i+1),f'斜辺²＝{3*(i+1)}²＋{4*(i+1)}²。長さは正なので{5*(i+1)}cm。',{'kind':'hypotenuse','legs':[3*(i+1),4*(i+1)]}))
math_unit(3,'sampling','標本調査',lambda i:(f'【仮想調査】ある集団から無作為に200人を調べると、{i+20}人がAを選んだ。集団全体が2000人のとき、同じ割合とみなしてAを選ぶ人数を推定しなさい。',(i+20)*10,f'標本の割合は{i+20}/200。2000×{i+20}/200＝{(i+20)*10}人と推定。推定値は真の人数を確定するものではない。',arithmetic(f'2000*{i+20}/200',0)))
# Actual science problems carry explicit idealized/fictional assumptions and units.
specs=[
 (1,'density','密度',lambda i:(f'【仮想測定】質量{(i+2)*8}g、体積{i+2}cm³の物体の密度は何g/cm³か。',8,f'質量÷体積＝{(i+2)*8}÷{i+2}＝8g/cm³。',f'{(i+2)*8}/{i+2}')),
 (1,'concentration','水溶液の濃度',lambda i:(f'【仮想調製】水{180-i*2}gに食塩{20+i*2}gを完全に溶かした。質量パーセント濃度を求めなさい（%）。',10+i,f'溶液は200g。溶質{20+i*2}÷200×100＝{10+i}%。',f'{20+i*2}/200*100')),
 (1,'solubility','溶解度・再結晶',lambda i:(f'【仮想物質A】水100gに溶ける最大量は高温で{50+i}g、低温で{20+i%6}g。高温の水100gにAを限界まで溶かして低温へ冷やした。水の蒸発がないとき析出するAは何gか。',30+i-i%6,f'水100gに対応する最大量の差。{50+i}－{20+i%6}＝{30+i-i%6}g。',f'{50+i}-{20+i%6}')),
 (1,'light','光の反射',lambda i:(f'平面鏡で入射光と法線のなす角が{i+10}°。反射光と法線のなす角は何度か。',i+10,'入射角と反射角は等しい。鏡面そのものからの角度とは区別する。',str(i+10))),
 (1,'sound','音の伝わり方',lambda i:(f'【仮想条件】音の速さを340m/sとする。光が見えてから音が聞こえるまで{i%5+1}秒。光の移動時間を無視すると、音源まで何mか。',340*(i%5+1),f'距離＝速さ×時間＝340×{i%5+1}＝{340*(i%5+1)}m。',f'340*{i%5+1}')),
 (1,'spring','力とばね',lambda i:(f'【仮想ばね・比例の範囲】0.2Nの力で{i%4+1}cm伸びるばねに0.8Nを加える。伸びは何cmか。',4*(i%4+1),f'力が4倍なので伸びも4倍。{i%4+1}×4＝{4*(i%4+1)}cm。',f'{i%4+1}*4')),
 (1,'earthquake','地震',lambda i:(f'【仮想記録】ある地点でP波が到着してから{i%8+2}秒後にS波が到着した。初期微動継続時間は何秒か。',i%8+2,'P波の到着からS波の到着までの時間が初期微動継続時間。',str(i%8+2))),
 (2,'chemical-mass','化学変化と質量',lambda i:(f'【仮想実験・密閉容器】反応前の容器と中身の総質量が{i+130}g。外部との物質の出入りがない化学反応後の総質量は何gか。',i+130,'密閉し物質の出入りがなければ、化学反応前後の総質量は変わらない。',str(i+130))),
 (2,'current','電流・抵抗',lambda i:(f'理想的な抵抗{i%8+2}Ωに{(i%8+2)*(i%4+1)}Vの電圧を加える。流れる電流は何Aか。',i%4+1,f'I＝V/R＝{(i%8+2)*(i%4+1)}÷{i%8+2}＝{i%4+1}A。',f'{(i%8+2)*(i%4+1)}/{i%8+2}')),
 (2,'power','電力・電力量',lambda i:(f'電圧{i+10}V、電流2Aで作動する電熱器の電力は何Wか。',2*(i+10),f'P＝VI＝{i+10}×2＝{2*(i+10)}W。',f'{i+10}*2')),
 (2,'humidity','湿度',lambda i:(f'【仮想気象条件】実際の水蒸気量が{i%5+1}g/m³、同じ温度の飽和水蒸気量が{(i%5+1)*4}g/m³。湿度は何%か。',25,'湿度＝実際の水蒸気量÷飽和水蒸気量×100。4分の1なので25%。',f'{i%5+1}/{(i%5+1)*4}*100')),
 (2,'weather','気象観測',lambda i:(f'【仮想観測】ある日の最高気温が{i+20}℃、最低気温が{i+7}℃だった。日較差は何℃か。',13,f'最高－最低＝{i+20}－{i+7}＝13℃。',f'{i+20}-{i+7}')),
 (3,'motion','運動の速さ',lambda i:(f'等速直線運動する台車が{(i+2)*3}mを3秒で進んだ。速さは何m/sか。',i+2,f'速さ＝距離÷時間＝{(i+2)*3}÷3＝{i+2}m/s。',f'{(i+2)*3}/3')),
 (3,'work','仕事',lambda i:(f'水平な床で物体に進む向きと同じ方向に{i+2}Nの一定の力を加え、5m動かした。この力がした仕事は何Jか。',5*(i+2),f'仕事＝力×力の向きに動いた距離＝{i+2}×5＝{5*(i+2)}J。',f'{i+2}*5')),
 (3,'energy','位置エネルギー',lambda i:(f'【仮想条件】100gの物体にはたらく重力を1Nとする。質量{(i+1)*100}gの物体を基準面から2mの高さに置いた。重力による位置エネルギーは何Jか。',2*(i+1),f'重力は{i+1}N。位置エネルギー＝重力×高さ＝{i+1}×2＝{2*(i+1)}J。',f'{i+1}*2')),
 (3,'ions','原子・イオン',lambda i:(f'陽子が{i%8+3}個、電子が{i%8+2}個の粒子がある。全体の電荷は素電荷を単位としていくつか。正の数は＋、負の数は－で答えなさい。',1,'陽子の数より電子の数が1少ないため、全体の電荷は＋1。',f'{i%8+3}-{i%8+2}')),
 (3,'inheritance','遺伝の規則性',lambda i:(f'【単純な仮想モデル】対立遺伝子A/aをもつ親Aaどうしを交配する。各親がA/aを等確率で伝えるとき、子がaaになる確率を小数で答えなさい。条件の確認番号{i+1}。',0.25,'各親からaを受け取る確率は各1/2。独立なので1/2×1/2＝1/4＝0.25。', '1/2*1/2')),
 (3,'astronomy','地球の自転・天体',lambda i:(f'地球の自転を24時間で360°の等速回転とみなす。{i%6+1}時間に回転する角度は何度か。',15*(i%6+1),'1時間あたり360÷24＝15°。これに時間をかける。',f'360/24*{i%6+1}'))]
for grade,unit,title,make in specs:
 families.append({'subject':'science','grade':grade,'unit':unit,'title':title,'instances':30,'family_count':1,'qualification':'idealized numerical family; producer checks only'})
 for i in range(30):
  p,a,e,expr=make(i);add('science',grade,unit,title,'science-'+unit,p,a,e,{'kind':'expression','expression':expr},case=i)
# Do not inflate count by appending arbitrary case numbers to identical science problems.
seen=set();unique=[]
for q in questions:
 key=(q['subject'],q['grade'],q['prompt'].split('条件の確認番号')[0])
 if key in seen:continue
 seen.add(key);q['prompt']=q['prompt'].split('条件の確認番号')[0].rstrip('。')+'。' if '条件の確認番号' in q['prompt'] else q['prompt'];unique.append(q)
questions=unique
(O/'questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2)+'\n');(O/'families.json').write_text(json.dumps(families,ensure_ascii=False,indent=2)+'\n')
with (O/'questions.csv').open('w',newline='') as f:
 keys=list(dict.fromkeys(k for q in questions for k in q));w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:json.dumps(q[k],ensure_ascii=False) if k in q else '' for k in keys} for q in questions)
print('question instances',len(questions),'authored families',len(families))
