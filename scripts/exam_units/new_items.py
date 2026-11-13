"""Focused practice for gaps in the first exam syllabus."""
from fractions import Fraction

from unit20.common import choice, number


def math_items(key):
    items = []
    for i in range(20):
        a, b = i % 5 + 2, i // 5 + 3
        x, y = i + 2, i % 7 + 1
        if key == 'sector':
            r, fraction = i+4, [2,3,4,6][i%4]
            angle = 360//fraction
            if i%2:
                result = Fraction(314,100)*r*r/fraction
                rounded = (result*100+Fraction(1,2))//1/100
                q = number(f'半径{r} cm、中心角{angle}°のおうぎ形の面積を求めよう。円周率は3.14とし、小数第3位を四捨五入して cm² で答える。',rounded,f'円の面積3.14×{r}²の{fraction}分の1。')
            else:
                result = Fraction(314,100)*2*r/fraction
                rounded = (result*100+Fraction(1,2))//1/100
                q = number(f'半径{r} cm、中心角{angle}°のおうぎ形の弧の長さを求めよう。円周率は3.14とし、小数第3位を四捨五入して cm で答える。',rounded,f'円周2×3.14×{r}の{fraction}分の1。')
        elif key == 'surface':
            c = i+4
            q = number(f'縦{a} cm、横{b} cm、高さ{c} cmの直方体の表面積は何cm²？',2*(a*b+b*c+c*a),
                       f'同じ面が2枚ずつ。2×({a}×{b}＋{b}×{c}＋{c}×{a})。')
        elif key == 'frequency':
            n = i+6
            q = number(f'【階級別人数】0以上10未満：{n}人／10以上20未満：{2*n}人／20以上30未満：{n+4}人。{10 if i%2 else 20}以上の人数は？',
                       (3*n+4) if i%2 else n+4, '条件を満たす階級の度数を合計する。')
        elif key == 'substitution':
            q = number(f'連立方程式 y＝{a}x−{a*x-y}、x＋y＝{x+y} を代入法で解こう。xの値は？',x,
                       f'第2式に第1式を代入すると {a+1}x＝{(a+1)*x}。')
        elif key == 'simultaneous-story':
            total = 130*x+70*y
            q = number(f'130円のノートと70円の鉛筆を計{x+y}個買い、{total}円払った。ノートは何冊？',x,
                       f'全部鉛筆なら{70*(x+y)}円。差を1個あたりの差60円で割る。')
        elif key == 'linear-form':
            m = (-1 if i%2 else 1)*a
            c = i-8
            q = number(f'一次関数のグラフが点 (2, {2*m+c}) と (5, {5*m+c}) を通る。式 y＝ax＋b の {"切片 b" if i%2 else "傾き a"} は？',
                       c if i%2 else m,f'傾きはyの増加量÷xの増加量で{m}。点 (2, {2*m+c}) を代入して切片は{c}。')
        elif key == 'linear-cross':
            q = number(f'料金Aは基本料{30*x}円と1個50円、料金Bは基本料なしで1個80円。料金が等しくなる個数は？',x,
                       f'{30*x}＋50x＝80x。基本料を単価の差30円で割る。')
        elif key == 'expansion':
            q = choice(f'(x＋{a})(x−{b}) を展開した式を選ぼう。',
                       f'x²＋({a-b})x−{a*b}',f'x²＋({a+b})x−{a*b}',f'x²＋({a-b})x＋{a*b}',
                       f'xの係数は{a}−{b}、定数項は{a}×(−{b})。')
        elif key == 'radicals':
            d = [2,3,5,6,7][i%5]
            q = choice(f'√{a*a*d}＋√{b*b*d} を簡単にした式は？',f'{a+b}√{d}',f'{a*b}√{d}' if a*b!=a+b else f'{a+b+1}√{d}',f'{a+b}√{2*d}',
                       f'√{a*a*d}＝{a}√{d}、√{b*b*d}＝{b}√{d}。根号の中が同じなので係数を足す。')
        elif key == 'quadratic-formula':
            d = [2,3,5,6,7][i%5]
            h = i//5+2
            c = h*h-d
            q = choice(f'二次方程式 x²−{2*h}x＋({c})＝0 の解を、解の公式で求めよう。',
                       f'x＝{h}±√{d}',f'x＝−{h}±√{d}',f'x＝{2*h}±√{d}',
                       f'判別式は{4*d}。分子は{2*h}±√{4*d}、分母は2。')
        elif key == 'quadratic-story':
            q = number(f'長方形の横は縦より{a} cm長く、面積は{x*(x+a)} cm²。縦は何cm？',x,
                       f'縦をtとすると t(t＋{a})＝{x*(x+a)}。正の解は{x}。')
        elif key == 'quadratic-graph':
            m = (-1 if i%2 else 1)*a
            q = number(f'放物線 y＝{m}x² 上の点 ({x}, {m*x*x}) と y軸に関して対称な点のx座標は？',
                       -x,'y軸に関して対称な点は、y座標が同じでx座標の符号が反対。')
        else:
            return []
        items.append(q)
    return items


def english_items(key):
    acts = [('the library','study'),('the pool','swim'),('the gym','practice'),('the station','meet my friend'),
            ('the shop','buy milk'),('the park','take pictures'),('the museum','see the paintings'),
            ('the kitchen','make lunch'),('the beach','watch the sunset'),('the bookstore','look for a dictionary')]
    pairs = [('letter','write'),('book','read'),('food','eat'),('song','sing'),('picture','draw'),
             ('video','watch'),('puzzle','solve'),('gift','send'),('room','clean'),('game','play')]
    people = ['Aki','Mika','Hana','Yuta','Ken','Nana','Ryo','Mei','Sora','Rio']
    out = []
    for i in range(20):
        j=i%10
        if key == 'infinitive-purpose':
            place,v=acts[j]
            start=f'I went to {place}' if i<10 else f'We will go to {place}'
            out.append(choice(f'{start} (　). 「～するために」を表す語句は？','to '+v,v,'of '+v,
                              '目的を表す不定詞は to＋動詞の原形。「～するために」。'))
        elif key == 'infinitive-noun':
            noun,v=pairs[j]
            out.append(choice(f'{"I have" if i<10 else "We need"} {"some" if noun=="food" else "a"} {noun} (　). 名詞を「～するための」と説明しよう。',
                              'to '+v,v,'will '+v,'名詞の直後の to＋動詞の原形が、その名詞を説明する。'))
        elif key == 'comparison':
            if i<10:
                out.append(choice(f'{people[j]} is (　) of the three. 「3人の中で最も背が高い」', 'the tallest','taller','as tall',
                                  '三者以上の中で最も～は the＋最上級で表す。'))
            else:
                out.append(choice(f'{people[j]} is as (　) as {people[(j+1)%10]}. 「同じくらい背が高い」','tall','taller','tallest',
                                  'as ～ as の間に形容詞の原級を置く。'))
        elif key == 'perfect-experience':
            destinations = ['Kyoto','Nara','Osaka','Hokkaido','Okinawa','Tokyo','Kobe','Sendai','Nagoya','Hiroshima']
            place = destinations[j]
            if i<10:
                out.append(choice(f'Have you (　) visited {place}? 「これまでに訪れたことがありますか」',
                                  'ever','since','ago','経験を尋ねる疑問文では ever が「これまでに」を表す。'))
            else:
                out.append(choice(f'{people[j]} has (　) to {place} twice. 「2回行ったことがある」',
                                  'been','go','going','have been to＋場所で「行ったことがある」。'))
        elif key == 'perfect-duration':
            if i<10:
                out.append(choice(f'{people[j]} has lived here (　) {j+2} years. 「{j+2}年間ずっと住んでいる」',
                                  'for','since','ago','期間を表す「～年間」には for を使う。'))
            else:
                out.append(choice(f'{people[j]} has lived here (　) {2010+j}. 「{2010+j}年からずっと住んでいる」',
                                  'since','for','ago','継続の起点を示す「～から」には since を使う。'))
        elif key == 'perfect-result':
            if i<10:
                out.append(choice(f'{people[j]} has (　) finished the task. 「もう課題を終えた」',
                                  'already','yet','since','肯定文の already は「もう、すでに」を表す。'))
            else:
                out.append(choice(f'{people[j]} has not finished the work (　). 「まだその作業を終えていない」',
                                  'yet','since','ago','否定文で「まだ」は文末の yet で表す。'))
        elif key == 'relative-object':
            noun,v=pairs[j]
            relative=f'the {noun} that I {v}' if i<10 else f'the {noun} that we can {v}'
            out.append(choice(f'「{relative}」で、that が後ろの節の中で果たす役割は？',
                              f'{v} の目的語','後ろの節の主語','動作が行われる場所を表す副詞',
                              f'後ろの節の主語は {"I" if i<10 else "we"}。先行詞 {noun} は {v} の対象に当たる。'))
        else:
            return []
    return out


def science_items(key):
    out=[]
    for i in range(20):
        a,b=i+3,i%5+2
        if key=='balance':
            out.append(number(f'机に置いた物体に鉛直下向きに{a} Nの重力が働く。物体は静止し、ほかに働くのは机からの垂直抗力だけ。この力は何N？',a,
                              '静止してつり合う二力は、大きさが同じで向きが反対。'))
        elif key=='ohm':
            if i%3==0:
                out.append(number(f'抵抗{a} Ωに{a*b} Vを加えた。電流は何A？',b,f'I＝V÷R＝{a*b}÷{a}。'))
            elif i%3==1:
                out.append(number(f'{a} Ωの抵抗器に{b/10:g} Aが流れる。両端の電圧は何V？',a*b/10,f'V＝RI＝{a}×{b/10:g}。'))
            else:
                out.append(number(f'抵抗器の電圧が{a*b} V、電流が{b} Aのとき、抵抗は何Ω？',a,f'R＝V÷I＝{a*b}÷{b}。'))
        elif key=='circuits':
            if i%2:
                out.append(number(f'{a} Ωと{2*a} Ωを並列につなぎ、両端に{2*a*b} Vを加えた。回路全体の電流は何A？',3*b,
                                  f'各枝に同じ電圧がかかる。枝の電流{2*b} Aと{b} Aの和をとる。'))
            else:
                out.append(number(f'{a} Ωと{2*a} Ωを直列につなぎ、全体に{3*a*b} Vを加えた。{2*a} Ωの両端の電圧は何V？',2*a*b,
                                  f'全体の抵抗は{3*a} Ω。電流は{b} Aなので、求める電圧は{2*a}×{b}。'))
        elif key=='electric-power':
            v=a+2; current=b/10; seconds=15+i*5
            if i%2:
                out.append(number(f'{v} Vで{current:g} Aが流れる電熱器を{seconds}秒使った。電力量は何J？',v*b*seconds/10,
                                  f'電力は{v}×{current:g} W。電力量(J)はその電力×{seconds}秒。'))
            else:
                out.append(number(f'{v*b} Wの器具を{v} Vで使った。電流は何A？',b,f'P＝VIなので、I＝{v*b}÷{v}。'))
        else:
            return []
    return out
