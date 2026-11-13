from fractions import Fraction
from math import sqrt
from .common import choice, number


def generate(unit, i):
    key = unit.removeprefix('math-')
    if key.startswith('class-math-'):
        grade, topic = key.removeprefix('class-math-g').split('-', 1)
        key = (grade, topic)
    n = i + 2
    if key == 'signed-meaning':
        if i % 3 == 0:
            return number(f'数直線上の −{n} と {n+2} の間の距離はいくつ？', 2*n+2, f'距離は大きい座標から小さい座標を引く。{n+2}−(−{n})＝{2*n+2}。')
        if i % 3 == 1:
            return choice(f'−{n} と −{n+3} の大小を比べよう。', f'−{n} ＞ −{n+3}', f'−{n} ＜ −{n+3}', f'−{n} ＝ −{n+3}', '数直線で右にある方が大きい。負の数どうしでは絶対値が小さい方が大きい。')
        return number(f'絶対値が {n} で、0 より小さい数を答えよう。', -n, f'0からの距離が{n}の数は±{n}。そのうち負の数を選ぶ。')
    if key == 'signed-addition':
        a,b=(-n,2*n+1) if i%2 else (-n,-2*n-1)
        op='−' if i%3==0 else '＋'
        ans=a-b if op=='−' else a+b
        return number(f'({a}) {op} ({b}) を計算しよう。',ans,f'引き算では引く数の符号を変えて足す。計算結果は {ans}。')
    if key == 'signed-products':
        a,b=(-n,3+i%5)
        if i%2:
            return number(f'({a*b}) ÷ ({a}) を計算しよう。',b,f'負÷負＝正。絶対値を割ると {b}。')
        return number(f'({a}) × {b} を計算しよう。',a*b,f'負×正＝負。{n}×{b}の結果に負の符号を付ける。')
    if key == 'signed-mixed':
        a=i%5+2
        if i%2:
            return number(f'({-a})² − {n} × 3 を計算しよう。',a*a-3*n,f'累乗と乗法を先に計算する。{a*a}−{3*n}。')
        return number(f'{n} ＋ ({-a})³ を計算しよう。',n-a**3,f'負の数の3乗は負。{n}−{a**3}。')
    if key == 'expression-writing':
        k=i+3
        if i%2:
            return choice(f'同じ長さのひも {k} 本で合計 x m。1本の長さを式で表すと？',f'x ÷ {k}',f'{k}x',f'{k} ÷ x',f'全体の長さ x を本数 {k} で割る。')
        return choice(f'1冊 x 円のノート {k} 冊と、60円の消しゴム1個の代金は？',f'{k}x＋60',f'x＋{k}＋60',f'60x＋{k}',f'ノート代が {k}x 円。そこに60円を足す。')
    if key == 'substitution':
        x=-n
        return number(f'x＝{x} のとき、2x²＋3x−1 の値を求めよう。',2*x*x+3*x-1,f'x²＝{x*x}、3x＝{3*x}。{2*x*x}＋({3*x})−1。')
    if key == 'like-terms':
        a=n+4;b=n-1
        return choice(f'{a}x − {b}x ＋ {n} を簡単にしよう。',f'{a-b}x＋{n}',f'{a-b+n}x',f'{a+b}x＋{n}',f'xの係数だけを引く。{a}−{b}＝{a-b}。定数{n}はそのまま。')
    if key == 'linear-equations':
        x=(-1)**i*n;a=i%4+3;b=n+5
        return number(f'{a}(x＋2) − x ＝ {((a-1)*x+2*a)}。xを求めよう。',x,f'左辺を展開すると {a-1}x＋{2*a}。両辺から{2*a}を引き、{a-1}で割る。')
    if key in ('equation-stories',('1','application')):
        if i%3==0:
            total=(n+4)*70+45
            return number(f'70円の品を何個かと45円の袋を1枚買い、{total}円払った。品はいくつ？',n+4,f'(合計−袋代)÷70＝({total}−45)÷70。')
        if i%3==1:
            return number(f'同じ速さで{5*n} mを5秒で歩く。{12*n} mを歩くのに何秒かかる？',12,f'速さは毎秒{n} m。{12*n}÷{n}＝12秒。')
        return number(f'姉は弟より4歳上で、2人の年齢の合計は{2*n+4}歳。弟は何歳？',n,f'弟をx歳とすると x＋(x＋4)＝{2*n+4}。')
    if key == 'proportion':
        if i%2:
            return number(f'y は x に反比例し、x＝{n} のとき y＝12。x＝{n*3} のときの y は？',4,'xが3倍になると、反比例するyは3分の1になる。')
        return number(f'y は x に比例し、x＝3 のとき y＝{3*n}。x＝−2 のときの y は？',-2*n,f'比例定数は{n}。y＝{n}xに−2を代入する。')
    if key in ('plane-angles',('1','geometry-data')):
        if i%3==0:
            a=n+24;b=n+38
            return number(f'三角形の二つの内角が {a}° と {b}°。残りの角は何度？',180-a-b,f'三角形の内角の和は180°。180−{a}−{b}。')
        if i%3==1:
            return number(f'半径{n} cm、中心角90°のおうぎ形の面積を求めよう。円周率は3.14とし、cm²で答える。',3.14*n*n/4,f'円の面積3.14×{n}²の4分の1。')
        return number(f'平行な2直線を1本の直線が横切る。同位角の一方が {n+62}° のとき、対応するもう一方は何度？',n+62,'平行線では同位角の大きさが等しい。')
    if key == 'plane-area':
        return number(f'上底 {n} cm、下底 {n+5} cm、高さ6 cmの台形の面積は何cm²？',3*(2*n+5),f'(上底＋下底)×高さ÷2＝({n}＋{n+5})×6÷2。')
    if key == 'solid-volume':
        h=n+3
        return number(f'底面積{3*n} cm²、高さ{h} cmのすい体の体積は何cm³？',n*h,f'底面積×高さ÷3＝{3*n}×{h}÷3。')
    if key == 'data-summary':
        values=[n+6,n,n+2,n+2,n+5]
        ask=['平均値','中央値','最頻値'][i%3]
        ans=[sum(values)/5,n+2,n+2][i%3]
        return number(f'測定値は {", ".join(map(str,values))}。{ask}を求めよう。',ans,
                      ['値の合計を5で割る。','小さい順に並べた中央の値。','出現回数が最も多い値。'][i%3]+f'答えは{ans:g}。')
    if key == 'percentage':
        price=n*250
        return number(f'{price}円の品物を12％引きで買う。支払う金額は何円？',price*88//100,f'定価の88％を払う。{price}×0.88。')
    if key == 'picnic-puzzles':
        if i%2:
            return number(f'ピクニックに{3*n+1}人が参加。1台に3人まで乗れるカートは最低何台必要？',n+1,f'{n}台では{3*n}人しか乗れない。残り1人にも1台必要。')
        return number(f'飲み物を1人350 mLずつ{n}人分用意する。1本700 mLのボトルは最低何本？',(n+1)//2,'1本で2人分。人数を2で割り、余りがあれば1本足す。')
    if key == ('2','application'):
        if i%2==0:
            return number(f'Aは2冊で{60*n+100}円、Bは1冊で{30*n}円。Aのノート1冊とBのノート1冊の価格差は何円？',50,'Aの2冊分からBの2冊分を引くと100円。1冊あたり50円。')
        return number(f'水槽に最初{n} L入っている。毎分3 Lずつ入れ、毎分1 Lずつ出す。{n+18} Lになるのは何分後？',9,'毎分2 L増える。必要な増加量は18 Lなので9分。')
    if key == ('2','reasoning'):
        if i%3==0:
            return number(f'赤{n}個、白{n}個の玉から1個を同様に確からしく引く。赤が出る確率を小数で答えよう。',.5,f'全{2*n}個のうち赤は{n}個。確率は1/2。')
        if i%3==1:
            return choice(f'平行四辺形ABCDの対角線ACの長さが{2*n} cm。対角線の交点Oについて正しいのは？',f'AO＝{n} cm',f'AO＝{2*n} cm',f'AO＝{3*n} cm','平行四辺形の対角線はそれぞれの中点で交わる。')
        return number(f'四分位数が第1＝{n}、第3＝{2*n+5}。四分位範囲は？',n+5,f'第3四分位数から第1四分位数を引く。{2*n+5}−{n}。')
    if key == ('3','application'):
        if i%3==0:
            return number(f'連続する正の整数の積が {n*(n+1)}。小さい整数を求めよう。',n,f'小さい整数をxとすると x(x＋1)＝{n*(n+1)}。{n}×{n+1}が条件に合う。')
        if i%3==1:
            return number(f'面積が {n*(n+3)} cm²の長方形で、横は縦より3 cm長い。縦は何cm？',n,f'縦をxとすると x(x＋3)＝{n*(n+3)}。長さなので正の解{n}。')
        return number(f'y＝{n}x²で、xが2から5まで増えるときの変化の割合は？',7*n,f'(25×{n}−4×{n})÷(5−2)＝{7*n}。')
    if key == ('3','reasoning'):
        if i%3==0:
            return number(f'同じ時刻、垂直に立つ2 mの棒の影は3 m。木の影が{3*n} mなら、木の高さは何m？ 地面は水平。',2*n,f'相似より影の比は1：{n}。高さも同じ比。')
        if i%3==1:
            return number(f'全校{50*n}人から無作為に50人を調べると、12人が徒歩通学だった。この割合を使って全校の徒歩通学者を何人と推定する？',12*n,f'標本の割合12/50を全体に掛ける。{50*n}×12/50。')
        return number(f'円の小さい方の弧ABに対する中心角は{4*n+24}°。大きい方の弧AB上にCを取る。∠ACBは何度？',2*n+12,'同じ弧に対する円周角は中心角の半分。')
    raise KeyError(unit)
