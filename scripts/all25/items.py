"""Additional exercises for the minimum bank size and expanded curriculum."""
from unit20.common import choice, number


def paired_items(rows):
    items = []
    for i, (answer, explanation) in enumerate(rows):
        others = {}
        for other, note in rows[i+1:]+rows[:i]:
            if other != answer and note != explanation:
                others.setdefault(other, note)
        if len(others) < 2:
            continue
        first, second = list(others.items())[:2]
        note = explanation.rstrip('。')
        items.extend([
            choice(f'【説明から選ぶ】\n{note}。これに当てはまるものは？',
                   answer, first[0], second[0], f'「{answer}」が当てはまる。{note}。'),
            choice(f'【用語の意味】\n「{answer}」について合う説明は？',
                   explanation, first[1], second[1], f'{note}。'),
            choice(f'【組み合わせ】\n「{answer}」の説明を確認しよう。組み合わせが正しいものは？',
                   f'{answer} ― {explanation}', f'{first[0]} ― {second[1]}',
                   f'{second[0]} ― {first[1]}', f'{note}。'),
        ])
    return items


def skills(key, n=25, offset=0):
    items = []
    for i in range(offset, offset+n):
        a, b = i//5+2, i%5+2
        if key == 'factorization':
            q = choice(f'x²＋{a+b}x＋{a*b} を因数分解しよう。',
                       f'(x＋{a})(x＋{b})', f'(x−{a})(x−{b})', f'(x＋{a})(x−{b})',
                       f'和が{a+b}、積が{a*b}となる二数は{a}と{b}。')
        elif key == 'quadratic-function':
            q = number(f'y＝{a}x² で、xが −{b+1} から −{b} まで増えるとき、変化の割合は？',
                       -a*(2*b+1), f'xの増加量は1。yの増加量は {a}×({b}²−{b+1}²)＝−{a*(2*b+1)}。')
        elif key == 'forces':
            q = number(f'台車に東向きに{2*a+b} N、西向きに{b} Nの力が働く。東向きを正とすると合力は何N？',
                       2*a, f'逆向きの二力なので、東向きの{2*a+b} Nから西向きの{b} Nを引く。')
        elif key == 'motion-data':
            dist = (i+2)*5+b
            q = number(f'0.2秒ごとに台車の位置を記録した。連続する2点の間隔が{dist} cmの区間の平均の速さは何cm/s？',
                       dist*5, f'間隔の距離を記録間隔0.2秒で割る。{dist}÷0.2＝{dist*5}。')
        elif key == 'power':
            f, d, t = (i+2)*3, a, b
            if i % 2:
                q = number(f'{f} Nの物体を鉛直に{d} m持ち上げるのに{t}秒かかった。平均の仕事率は何W？ 小数第2位を四捨五入。',(20*f*d+t)//(2*t)/10,
                           f'仕事率＝仕事÷時間。{f}×{d}÷{t}で求める。')
            else:
                q = number(f'重さ{2*f} Nの荷物を鉛直に{d} m上げる。理想的な動滑車で力の大きさが半分になったとき、ひもを何m引く？',2*d,
                           f'仕事の原理で {2*f}×{d}＝{f}×引く距離。力を半分にすると距離は2倍。')
        elif key == 'mechanical':
            initial, final = 10*(i+3), 4*(i+3)
            q = number(f'球が静止から転がり始めた。開始時の位置エネルギーは{initial} J、途中で{final} Jになった。摩擦や回転の影響を考えず、失われた位置エネルギーがすべて運動エネルギーになったとすると、運動エネルギーは何J？',
                       initial-final, f'力学的エネルギーが保存され、位置エネルギーの減少分 {initial}−{final} が運動エネルギーになる。')
        elif key == 'proportion-graph':
            c = i+3
            if i%2:
                q = number(f'反比例のグラフが点 ({b}, {c}) を通る。y＝k/x の比例定数kは？',b*c,f'反比例ではxyが一定。k＝{b}×{c}。')
            else:
                q = number(f'比例のグラフが点 ({b}, −{b*c}) を通る。y＝kx の比例定数kは？',-c,f'yをxで割る。−{b*c}÷{b}＝−{c}。')
        elif key == 'relative-frequency':
            first, second, total = i+3, i+8, 100
            if i%2:
                q = number(f'【度数】0以上10未満：{first}、10以上20未満：{second}、20以上30未満：{total-first-second}。最初の階級の相対度数を小数で答えよう。', first/total,
                           f'相対度数＝階級の度数÷全体の度数。{first}÷{total}。')
            else:
                q = number(f'【度数】0以上10未満：{first}、10以上20未満：{second}、20以上30未満：{total-first-second}。20未満までの累積度数は？', first+second,
                           f'20未満の階級を合計する。{first}＋{second}。')
        elif key == 'parallel-ratio':
            q = number(f'三角形ABCで点Dは辺AB上、点Eは辺AC上にあり、DE∥BC。AD＝{a} cm、DB＝{b} cm、AE＝{3*a} cm のとき、ECは何cm？',
                       3*b, f'平行線と線分の比より AD:DB＝AE:EC。AEはADの3倍なので、ECはDBの3倍。')
        elif key == 'diagonal':
            if i%2:
                q = number(f'直方体の底面の対角線は{3*b} cm、高さは{4*b} cm。底面から上面の向かいの角に引いた空間対角線は何cm？',5*b,
                           f'底面の対角線と高さは垂直。√(({3*b})²＋({4*b})²)＝{5*b}。')
            else:
                k = i+2
                q = number(f'長方形の縦が{5*k} cm、横が{12*k} cm。対角線は何cm？',13*k,
                           f'直角三角形の斜辺。√(({5*k})²＋({12*k})²)＝{13*k}。')
        else:
            return []
        items.append(q)
    return items


def unreal_items():
    situations = [('had a camera','take a picture','カメラがあれば写真が撮れるのに'),
                  ('had a bicycle','ride to school','自転車があれば自転車で登校できるのに'),
                  ('knew her address','write to her','住所を知っていれば彼女に手紙を書けるのに'),
                  ('had more time','read another book','時間がもっとあれば別の本を読めるのに'),
                  ('lived near the sea','swim every day','海の近くに住んでいたら毎日泳げるのに'),
                  ('had a map','find the park','地図があれば公園を見つけられるのに'),
                  ('knew the answer','tell you','答えを知っていれば教えられるのに'),
                  ('had a ticket','go to the concert','券があればコンサートに行けるのに'),
                  ('spoke French','talk with her','フランス語を話せれば彼女と会話できるのに')]
    out = []
    for condition, action, japanese in situations:
        out.extend([
            choice(f'「{japanese}」\nIf I (　), I could {action}.', condition,
                   condition.replace(' ', ' not ', 1), 'will '+condition,
                   '現在の事実と異なる仮定は if 節に動詞の過去形を使う。'),
            choice(f'「{japanese}」\nIf I {condition}, I (　) {action}.', 'could', 'am', 'had',
                   '仮定法では、結論に could＋動詞の原形を使うと「〜できるのに」を表せる。'),
            choice(f'If I {condition}, I could {action}.\nこの英文の時制の働きとして適切なのは？',
                   '今はそうではない状況を仮定している。','過去に実際に起きた二つの出来事を述べている。',
                   '将来に起きることを確約している。','if 節の過去形と could によって現在の事実に反する仮定を表す。')
        ])
    return out
