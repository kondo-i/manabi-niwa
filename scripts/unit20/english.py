from .common import choice, word

NAMES = ['Mika', 'Ryo', 'Aki', 'Ken', 'Sora', 'Nana', 'Mei', 'Yuta', 'Hana', 'Rio',
         'Tomo', 'Kota', 'Yui', 'Kumi', 'Nori', 'Haru', 'Rei', 'Kai', 'Ren', 'Mao']
PLACES = ['the library', 'the park', 'the station', 'the museum', 'the gym',
          'the school', 'the bookstore', 'the hospital', 'the river', 'the zoo',
          'the pool', 'the shop', 'the office', 'the theater', 'the hotel',
          'the bus stop', 'the bank', 'the bakery', 'the post office', 'the gate']
JP_PLACES = ['図書館', '公園', '駅', '博物館', '体育館', '学校', '本屋', '病院', '川', '動物園',
             'プール', '店', '事務所', '劇場', 'ホテル', 'バス停', '銀行', 'パン屋', '郵便局', '門']
ACTS = [('clean', 'the room', '部屋を掃除する'), ('wash', 'the dishes', '皿を洗う'),
        ('watch', 'the game', '試合を見る'), ('visit', 'the museum', '博物館を訪れる'),
        ('help', 'a friend', '友達を助ける'), ('open', 'the door', 'ドアを開ける'),
        ('close', 'the window', '窓を閉める'), ('play', 'the piano', 'ピアノを弾く'),
        ('study', 'English', '英語を勉強する'), ('paint', 'the wall', '壁を塗る'),
        ('cook', 'dinner', '夕食を作る'), ('finish', 'the homework', '宿題を終える'),
        ('call', 'the teacher', '先生に電話する'), ('water', 'the flowers', '花に水をやる'),
        ('carry', 'the bag', 'かばんを運ぶ'), ('check', 'the answer', '答えを確認する'),
        ('use', 'the computer', 'コンピューターを使う'), ('move', 'the chair', 'いすを動かす'),
        ('read', 'the book', 'その本を読む'), ('make', 'a cake', 'ケーキを作る')]
VOCAB = {
 'school-words': '黒板:blackboard 消しゴム:eraser 定規:ruler ノート:notebook はさみ:scissors 教室:classroom 辞書:dictionary 生徒:student 地図:map 鉛筆:pencil 机:desk いす:chair 宿題:homework 質問:question 答え:answer 窓:window ドア:door 授業:lesson 学校:school 図書館:library',
 'daily-words': '雲:cloud 雪:snow 風:wind 星:star 月:moon 川:river 山:mountain 湖:lake 森:forest 島:island 庭:garden 夕食:dinner 昼食:lunch 朝食:breakfast 夜:night 春:spring 夏:summer 秋:autumn 冬:winter 太陽:sun',
 'action-words': '歩く:walk 泳ぐ:swim 飛ぶ:fly 座る:sit 立つ:stand 待つ:wait 聞く:listen 描く:draw 書く:write 読む:read 洗う:wash 掃除する:clean 開ける:open 閉める:close 尋ねる:ask 教える:teach 学ぶ:learn 運ぶ:carry 買う:buy 売る:sell',
 'adjective-words': '忙しい:busy 有名な:famous 静かな:quiet 若い:young 暗い:dark 速い:fast 遅い:slow 長い:long 短い:short 新しい:new 古い:old 強い:strong 弱い:weak 安全な:safe 危険な:dangerous 幸せな:happy 悲しい:sad 簡単な:easy 難しい:difficult 重要な:important',
}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
          'September', 'October', 'November', 'December']


def ing(v):
    return v[:-1]+'ing' if v.endswith('e') else v+'ing'


def past(v):
    return {'study':'studied','carry':'carried','read':'read','make':'made'}.get(v, v+('d' if v.endswith('e') else 'ed'))


def third(v):
    return v[:-1]+'ies' if v.endswith('y') and v[-2] not in 'aeiou' else v+('es' if v.endswith(('sh','ch','s','x','z','o')) else 's')


def generate(unit, i):
    if unit.startswith(('exp-english-', 'class-english-')):
        grade, key = unit.split('-g',1)[1].split('-',1)
    else:
        key=unit.removeprefix('english-')
        grade='3' if key in ('passive-context','perfect-context') else '2' if key=='little-notes' else '1'
    # Reserve different source sentences for overlapping legacy and classroom units.
    j = (i + (0 if unit.startswith('class-') else 7 if unit.startswith('exp-') else 13)) % len(NAMES)
    who, place, jp = NAMES[j], PLACES[j], JP_PLACES[j]
    v, obj, action = ACTS[j]
    vp, vi, vs = past(v), ing(v), third(v)
    blank='(　)'
    if key in VOCAB:
        term, eng = VOCAB[key].split()[j].split(':')
        return word(f'「{term}」を表す英単語を1語で書こう。{eng[0]}で始まる{len(eng)}文字。',eng,f'{eng} は「{term}」を表します。',True)
    if key=='month-words':
        k=i%12
        if i%2:
            return word(f'{k+1}月の英語名を書こう。',MONTHS[k],f'{k+1}月は {MONTHS[k]}。月名の最初は大文字で書きます。',True)
        return choice(f'{MONTHS[k]} は何月？',f'{k+1}月',f'{(k+1)%12+1}月',f'{(k+10)%12+1}月',f'{MONTHS[k]} は{k+1}月です。')
    if key in ('be-verbs','be'):
        subj,ans=[('I','am'),(who,'is'),(f'{who} and I','are')][i%3]
        a,b=[x for x in ('am','is','are') if x!=ans]
        return choice(f'{subj} {blank} near {place} now. 空欄に入るbe動詞は？',ans,a,b,f'主語は {subj} なので {ans} を使います。')
    if key in ('general-verbs','present'):
        if i%3==0: return choice(f'{who} {blank} {obj} on Sundays.',vs,v,vi,'三人称単数の主語がする習慣は、現在形で動詞に s や es を付けます。')
        if i%3==1: return choice(f'Does {who} {blank} {obj} every week?',v,vs,vi,'Does の後ろの動詞は原形です。')
        return choice(f'{who} does not {blank} {obj} every day.',v,vs,vi,'does not の後ろには動詞の原形を置きます。')
    if key in ('questions','question-words'):
        questions=[(f'{blank} is {who}? — At the entrance to {place}.','Where','When','How many','場所'),
                   (f'{blank} does {who} get up? — At seven.','What time','Where','Who','時刻'),
                   (f'{blank} does {who} go to {place}? — By bus.','How','Who','What time','手段'),
                   (f'{blank} is with {who}? — My sister.','Who','When','Where','人'),
                   (f'{blank} pens does {who} have? — Three.','How many','How old','What time','数')]
        p,a,b,c,kind=questions[i%len(questions)]
        return choice(p,a,b,c,f'答えは{kind}を表します。それを尋ねる疑問詞は {a} です。')
    if key=='word-order':
        return choice(f'「{who}は毎日{jp}に行きます」に合う文は？',
                      f'{who} goes to {place} every day.',f'Goes {who} to {place} every day.',f'{who} to {place} goes every day.','ふつうの文では、主語の直後に動詞を置きます。')
    if key in ('pronouns',):
        a,b,c=[('us','we','our'),('them','they','their'),('me','I','my')][i%3]
        ref=['私たち','彼ら','私'][i%3]
        return choice(f'{who} goes to {place} with {blank}. 「{ref}と一緒に」の空欄は？',a,b,c,f'前置詞 with の後ろには目的格の {a} を置きます。')
    if key=='nouns-articles':
        terms=[('apple','an'),('pen','a'),('orange','an'),('book','a'),('egg','an'),('desk','a'),('umbrella','an'),('cap','a'),('eraser','an'),('ruler','a'),('hour','an'),('student','a')]
        noun,a=terms[i%len(terms)]
        return choice(f'{who} found {blank} {noun}.' if noun!='hour' else f'{who} waited for {blank} {noun}.',a,'a' if a=='an' else 'an','many',f'発音の最初が{"母音" if a=="an" else "子音"}なので {a} を使います。')
    if key in ('progressive','past-progressive'):
        time='when I arrived' if key.startswith('past') else 'at this moment' if unit.startswith('class-') else 'right now'
        be='was' if key.startswith('past') else 'is'
        return choice(f'{who} {be} {blank} {obj} {time}.',vi,v,vs,f'{be}＋動詞のing形で、{"過去のある時点で" if be=="was" else "今"}進行中の動作を表します。')
    if key=='place-prepositions':
        a,b,c,jp_pos=[('under','on','in','下'),('in','under','on','中'),('on','in','under','上')][i%3]
        return choice(f'{who} のペンは箱の{jp_pos}にある。The pen is {blank} the box.',a,b,c,f'{a} the box は「箱の{jp_pos}」です。')
    if key in ('passive','passive-context'):
        nouns=[('the gate','close','closed'),('the floor','clean','cleaned'),('the book','write','written'),
               ('the bridge','build','built'),('the picture','take','taken'),('the meal','make','made'),
               ('the bike','fix','fixed'),('the song','sing','sung'),('the box','open','opened'),('the letter','send','sent'),
               ('the window','break','broken'),('the door','paint','painted'),('the room','use','used'),
               ('the table','move','moved'),('the key','find','found')]
        noun,verb,pp=nouns[i%len(nouns)]
        return choice(f'Yesterday, {noun} was {blank} by {who}.',pp,verb,ing(verb),'受け身の形は be動詞＋過去分詞です。')
    if key in ('perfect-context','present-perfect','perfect-progressive'):
        if key=='perfect-progressive':
            return choice(f'{who} has been {blank} {obj} for an hour.',vi,v,vs,'現在完了進行形は have／has been＋動詞のing形です。')
        if i%3==0: return choice(f'{who} has lived in this town {blank} {2003+i}.','since','for','ago','継続の起点には since を使います。')
        if i%3==1: return choice(f'{who} has lived in this town {blank} {i+2} years.','for','since','ago','継続の長さには for を使います。')
        return choice(f'{who} has already {blank} {obj}.',vp,vs,vi,'has の後ろには過去分詞を置きます。')
    if key in ('can','must','future','imperative','gerund','infinitive','participle'):
        a,b,c,p,e={
            'can':(v,vs,vi,f'{who} can {blank} {obj}.','can の直後は動詞の原形です。'),
            'must':(v,vs,vi,f'{who} must {blank} {obj} before noon.','must の直後は動詞の原形です。'),
            'future':(v,vs,vi,f'{who} is going to {blank} {obj} tomorrow.','be going to の後ろは動詞の原形です。'),
            'imperative':(v.capitalize(),vs.capitalize(),vi.capitalize(),f'「{action}」という指示を英語で表そう。{blank} {obj}, {who}.','肯定の命令文は動詞の原形で始めます。'),
            'gerund':(vi,v,'to '+v,f'{who} finished {blank} {obj}.','finish の後ろに動作を続けるときは動名詞を使います。'),
            'infinitive':('to '+v,v,vp if vp != v else vi,f'{who} decided {blank} {obj}.','decide to＋動詞の原形で「～することに決める」です。'),
            'participle':(vi,v,vs,f'The person {blank} {obj} is {who}. 「～している人」を表そう。','現在分詞が後ろから person を修飾します。'),
        }[key]
        return choice(p,a,b,c,e)
    if key=='past':
        return choice(f'{who} {blank} {obj} yesterday.',vp,vs,vi,f'yesterday は過去。{v} の過去形は {vp} です。')
    if key=='there':
        a,b=('is','are') if i%2 else ('are','is')
        noun='a bus' if i%2 else f'{i+2} buses'
        return choice(f'There {blank} {noun} near {place}.',a,b,'am','There is／are の後ろに来る名詞が単数か複数かを見ます。')
    if key=='comparison':
        pairs=[('tall','taller','tallest'),('fast','faster','fastest'),('old','older','oldest'),('young','younger','youngest'),('short','shorter','shortest')]
        base,a,c=pairs[i%len(pairs)]
        return choice(f'{who} is {blank} than {NAMES[(j+1)%20]}.',a,base,c,'than の前には比較級を置きます。')
    if key=='conjunction':
        a,b,c,jp_link=[('because','when','if','～なので'),('when','if','because','～したとき'),('if','because','when','もし～なら')][i%3]
        return choice(f'「{jp_link}」を表そう。{who} goes to {place} {blank} there is a meeting.',a,b,c,f'{a} はここでは「{jp_link}」を表します。')
    if key=='indirect':
        return choice(f'Do you know {blank} after school? （{who}が放課後どこへ行くか）',f'where {who} goes',f'where does {who} go',f'where goes {who}','間接疑問は 疑問詞＋主語＋動詞 の順です。')
    if key=='relative':
        return choice(f'{who} is the student {blank} helped me near {place}.','who','which','what','先行詞が人で、関係節の主語に当たるので who を使います。')
    if key=='wish':
        return choice(f'「{who}が今、もっと近くに住んでいればいいのに」 I wish {who} {blank} closer.', 'lived','lives','is living','現実と異なる現在の願いを I wish＋主語＋過去形で表します。')
    if key in ('reading','little-notes','listening'):
        a=7+i%5; b=a+1
        if grade=='1':
            passage=f'Meet me near {place} at {a}. Please bring a pencil.'
            jp_prompt='どの場所の近くに集合する？'; ans=jp; wrong=[JP_PLACES[(j+1)%20],JP_PLACES[(j+2)%20]]
            explain=f'near {place} は「{jp}の近く」を表します。'
        elif grade=='2':
            passage=f'We planned to meet at {a}. The bus is late, so let us meet at {b} instead.'
            jp_prompt='変更後の集合時刻は？';ans=f'{b}時';wrong=[f'{a}時',f'{b+1}時']
            explain=f'instead は「代わりに」。後に述べた時刻は{b}時です。'
            passage+=f' We will wait near {place}.'
        else:
            passage=f'{who} wanted to walk to {place}. It started to rain, so {who} took a bus instead.'
            jp_prompt=f'{who}がバスを利用した理由は？';ans='雨が降り始めたから';wrong=['道を間違えたから','バスの運賃が無料だったから']
            explain='It started to rain. がバスを使うことにした理由です。'
        if i%3==1:
            passage=f'On Saturday we will meet at {place}. Please bring a notebook. A pen will be provided.'
            jp_prompt=f'{jp}へ行くときに持参する物は？';ans='ノート';wrong=['ペン','定規']
            explain='Please bring a notebook. が持参する物の指示です。'
        if i%3==2:
            passage=f'The event near {place} starts at {a}. Please arrive one hour early.'
            jp_prompt=f'{jp}の行事に着くよう指定された時刻は？';ans=f'{a-1}時';wrong=[f'{a}時',f'{a+1}時']
            explain=f'one hour early は「1時間早く」。開始は{a}時なので{a-1}時です。'
        if key=='listening':
            return choice(f'音声を聞いて答えよう。{jp_prompt}（場面：{jp}）',ans,*wrong,explain,transcript=passage)
        return choice(f'【案内・メモ】{passage}\n{jp_prompt}',ans,*wrong,explain)
    if key=='speaking':
        if grade=='1':
            return choice(f'「{action}のを手伝ってくれる？」と声に出してから、合う英文を選ぼう。',
                          f'Can you help me {v} {obj}?',f'Did you {v} {obj}?',f'I do not want to {v} {obj}.','Can you help me＋動詞の原形？で手伝いを頼めます。')
        if grade=='2':
            return choice(f'「一緒に{jp}へ行きませんか」と提案しよう。',f'Why do we go to {place}?'.replace('Why do we','Why don’t we'),f'When did we go to {place}?',f'Who goes to {place}?','Why don’t we ...? は一緒にする提案です。')
        return choice(f'「雨が降ったら{jp}へ行こう」と声に出してから、合う英文を選ぼう。',f"If it rains, let's go to {place}.",f"Although it rained, we left {place}.",f"Before it rains, we must leave {place}.",'If の節が条件、let’s の部分が提案です。')
    if key=='writing':
        if grade=='1':
            return word(f'{who} {blank} {obj} every week. 括弧の動詞を適切な現在形にして入力しよう。（{v}）',vs,f'{who} は三人称単数。現在形は {vs} です。',True)
        if grade=='2':
            return word(f'{who} was {blank} {obj} at seven last night. 括弧の動詞を適切な形にして入力しよう。（{v}）',vi,f'過去進行形は was＋ing形。{v} は {vi} になります。',True)
        return word(f'{who} has already {blank} {obj}. 括弧の動詞を過去分詞にして入力しよう。（{v}）',vp,f'{v} の過去分詞は {vp}。has の後ろに置きます。',True)
    raise KeyError(unit)
