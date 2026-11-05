"""Build revised social questions and a separate reviewable app-content draft."""
import copy
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOCIAL = ROOT / 'data/social/v3'
APP = ROOT / 'reports/app_review/v3'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def export_questions(folder, questions):
    write_json(folder / 'questions.json', questions)
    write_csv(folder / 'questions.csv', [{key: encode(value) for key, value in question.items()} for question in questions])
    lines = ['# 独立再監査用の教材ドラフト', '']
    for question in questions:
        choices = question['choices']
        answer = question.get('correct_index', question.get('answer'))
        lines.extend([f'## {question["id"]}', question['prompt'], '',
                      *[f'{index}. {choice}' for index, choice in enumerate(choices, 1)], '',
                      f'正答 {answer + 1}. {choices[answer]}', question['explanation'], ''])
        for hint in question.get('hints', []):
            lines.append('ヒント ' + hint)
    (folder / 'questions.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')


def change_rows(before, after):
    previous = {question['id']: question for question in before}
    rows = []
    for question in after:
        old = previous.get(question['id'])
        if old is None:
            rows.append({'id': question['id'], 'operation': 'add', 'field': '__item__', 'before': 'null', 'after': encode(question)})
            continue
        for field in dict.fromkeys([*old, *question]):
            if old.get(field) != question.get(field):
                rows.append({'id': question['id'], 'operation': 'modify', 'field': field,
                             'before': encode(old.get(field)), 'after': encode(question.get(field))})
    return rows


def make_social():
    old = load(ROOT / 'data/social/v2/questions.json')
    questions = copy.deepcopy(old)
    by_id = {question['id']: question for question in questions}
    for question in questions:
        question['furigana_policy'] = 'none_by_user_request_20261105'
        question['grade_policy'] = 'publisher_confirmed_edition_specific_alignment_pending'
    for id in ['SOC-HIS-007', 'SOC-HIS-008']:
        by_id[id]['grade'] = 3
        by_id[id]['grade_policy'] = 'tokyo_shoseki_r7_public_plan_reference_grade3_school_edition_pending'
    history = by_id['SOC-HIS-010']
    history['distractor_notes'] = [
        {'choice': '国民', 'reason': 'この憲法では、主権者が国民とされたわけではない。'},
        {'choice': '帝国議会', 'reason': '帝国議会は法律案などの審議に関わったが、統治権の総攬者ではない。'},
    ]
    history['explanation'] = '大日本帝国憲法では、天皇が統治権を総攬する天皇主権の仕組みとされた。'
    history['source_ids'] = ['MEIJI_TEXT', 'MEIJI_CONST']
    current = by_id['SOC-CIV-001']
    current['explanation'] = ('日本国憲法の前文と第1条は、主権が国民にあることを示す。'
                              '大日本帝国憲法の天皇主権と、日本国憲法の国民主権を比べて区別しよう。')
    current['source_ids'] = ['CONST', 'MEIJI_TEXT']
    rights = by_id['SOC-CIV-008']
    rights['choices'] = ['希望する品物を無料で受け取る権利がある', '働かなくても同じ収入を受け取る権利がある',
                         '健康で文化的な最低限度の生活を営む権利がある']
    rights['correct_index'] = 2
    rights['correct_answer'] = rights['choices'][2]
    rights['distractor_notes'] = [
        {'choice': rights['choices'][0], 'reason': '希望する品物を無料で受け取ることを定めた条文ではない。'},
        {'choice': rights['choices'][1], 'reason': '人の収入を同額にする権利を定めた条文ではない。'},
    ]
    rights['explanation'] = '日本国憲法第25条は、健康で文化的な最低限度の生活を営む権利を保障する。'
    for question in [history, current, rights]:
        question['explanation'] += ' 誤答の確認：' + ' '.join(
            f'「{note["choice"]}」は{note["reason"]}' for note in question['distractor_notes'])

    def new_question(id, field, grade, prompt, choices, correct, explanation, reasons, sources, hints):
        return {
            'id': id, 'subject': '社会', 'field': field, 'grade': grade,
            'grade_policy': 'publisher_confirmed_edition_specific_alignment_pending',
            'furigana_policy': 'none_by_user_request_20261105',
            'question_type': 'single_choice', 'prompt': prompt, 'choices': choices,
            'correct_index': correct, 'correct_answer': choices[correct],
            'explanation': explanation + ' 誤答の確認：' + ' '.join(
                f'「{choices[index]}」は{reason}' for index, reason in reasons.items()),
            'distractor_notes': [{'choice': choices[index], 'reason': reason} for index, reason in reasons.items()],
            'source_ids': sources, 'hints': hints, 'review_status': 'draft_awaiting_claude_independent_review',
            'release_status': 'not_published',
        }
    questions.extend([
        new_question('SOC-GEO-011', 'geography', 2,
                     '同じ地形図の中で、等高線の間隔がせまい場所は、間隔が広い場所と比べて傾斜がどうなっているか。',
                     ['急である', 'ゆるやかである', '平らである'], 0,
                     '等高線は同じ高さの点を結ぶ線。同じ高さの差を短い水平距離で上る場所ほど、傾斜が急になる。',
                     {1: '間隔が広い場所の特徴。', 2: '等高線がせまく並ぶ場所には高低差がある。'},
                     ['GSI_CONTOUR'], ['線と線の間で変わる高さは、同じ地形図なら同じだよ。', 'せまい場所で同じ高さを上ると、坂はどうなるかな。']),
        new_question('SOC-HIS-011', 'history', 2,
                     '【制度の違いを学ぶための要約】資料A「収穫した米の一部を納める」。資料B「土地の値段をもとに、お金で納める」。AからBへの変化に関係する改革はどれか。',
                     ['廃藩置県', '地租改正', '学制'], 1,
                     '米で納める物納から、地価を基準にお金で納める金納へ改めたのが地租改正。要約文は原史料からの直接引用ではない。',
                     {0: '藩を廃して県を置く地方制度の改革。', 2: '学校教育の制度に関わるもの。'},
                     ['TAX', 'HAN', 'TIMELINE'], ['二つの資料で、何を納めるかが変わっているよ。', '土地の値段と、お金で納める仕組みが手がかり。']),
    ])
    sources = copy.deepcopy(load(ROOT / 'data/social/v2/sources.json'))
    sources['checked_date_jst'] = '2026-11-05'
    sources['sources']['GSI_CONTOUR'] = {
        'title': '国土地理院 地図記号と地形図の読み方',
        'url': 'https://www.gsi.go.jp/common/000082924.pdf',
        'basis': '等高線で地形を読む箇所。線の間隔が狭いほど急、広いほど緩やか。制作側がPDF本文を確認。',
    }
    SOCIAL.mkdir(parents=True, exist_ok=True)
    export_questions(SOCIAL, questions)
    write_json(SOCIAL / 'sources.json', sources)
    write_csv(SOCIAL / 'change_map_v2_v3.csv', change_rows(old, questions))
    write_json(SOCIAL / 'textbook_policy.json', {
        'decided_on': '2026-11-05', 'furigana': 'none',
        'publishers': {'geography': '帝国書院', 'history': '東京書籍', 'civics': '日本文教出版'},
        'edition_status': 'unspecified_by_user',
        'reference_edition_for_public_unit_plans': '令和7年度版（参考用。使用版と同一との確認は未了）',
        'textbook_unit_mapping': 'see reports/textbook_alignment_20261105.md',
    })
    return questions


def make_app():
    previous = load(ROOT / 'reports/app_review/added_185_questions.json')
    items = copy.deepcopy(previous)
    by_id = {item['question']['id']: item for item in items}
    proposals = load(ROOT / 'reports/app_review/proposed_question_changes.json')
    for proposal in proposals:
        by_id[proposal['id']]['question'] = copy.deepcopy(proposal['after'])

    def edit(id, prompt, choices, answer, explanation, hints=None, skill=None):
        question = by_id[id]['question']
        question.update(prompt=prompt, choices=choices, answer=answer, explanation=explanation)
        if hints is not None:
            question['hints'] = hints
        if skill:
            question['skill'] = skill

    edit('japanese-g2-honorific-context-balance-001:q1',
         '明日、先生が教室に行く。「行く」を先生への敬意を表す形に変えるとどれか。',
         ['いらっしゃる', '参る', '申す'], 0,
         '先生の「行く」動作への敬意を表す尊敬語は「いらっしゃる」。「参る」は自分側の行く・来る動作の謙譲表現。「申す」は言う動作の謙譲語。')
    edit('japanese-g2-honorific-context-balance-001:q9',
         '生徒が友達に、先生が今どこにいるかを伝える。「先生は今、教室に（　）」の空欄に入る、先生への敬意を表す言い方はどれか。',
         ['おります', 'ございます', 'いらっしゃいます'], 2,
         '先生の「いる」を高める言い方は「いらっしゃいます」。「おります」は自分側に用いる丁重な言い方。「ございます」は人がいることへの尊敬表現には使わない。')
    edit('japanese-g2-auxiliary-context-balance-001:q4',
         '「先生が明日の予定を話される」の「れる」と同じ用法の文はどれか。',
         ['校長先生が玄関に立たれる', '妹が犬に追いかけられる', '昔の景色が自然と思い出される'], 0,
         '「話される」と「立たれる」は、先生の動作への敬意を表す尊敬。「追いかけられる」は受け身、「思い出される」は自然に気持ちが起こる自発。')
    edit('social-g1-geography-data-balance-001:q10',
         '【架空の地図資料】縮尺は5万分の1。地図上の6cmは実際には何kmか。',
         ['3km', '0.3km', '30km'], 0,
         '6×50,000＝300,000cm＝3km。1kmは100,000cmなので、300,000を100,000で割る。')
    edit('stretch-japanese-20261103:q2',
         '委員会の決まりに「雨の日は体育館を使う。ただし、舞台の準備がある日は別の場所を使う」とある。今日は雨で、舞台の準備がある。決まりに合う判断は？',
         ['別の場所を使う', '雨なので体育館を使う', '雨なので委員会の決まりを取り消す'], 0,
         '「ただし」の後に例外の条件がある。今日はその条件に当てはまるので、雨でも別の場所を使う。決まり全体を取り消すとは書かれていない。',
         ['「ただし」の後に注目しよう。', '舞台の準備がある日は、雨の日の決まりより例外を優先するよ。'], '例外条件を文脈に適用する')
    edit('stretch-japanese-20261103:q3',
         '校庭に赤いボールと白いボールがあった。太郎は赤いボールを拾った。「それは昨日、先生が使っていた物だ」と言った。「それ」が指すものはどれか。',
         ['赤いボール', '白いボール', '校庭'], 0,
         '太郎が拾って話題にしたのは赤いボール。その直後の「それ」は、話題になっている赤いボールを指す。',
         ['太郎が何を拾ったか、確かめよう。', '「それ」の直前で話題になっている物を探そう。'], '話題の流れから指示語をたどる')
    edit('stretch-japanese-20261103:q5',
         '「先生は『発表する人は、明日決めます』と言った。私は、きっと自分が選ばれると思った。」本文の事実と推測を分けた説明として適切なのは？',
         ['先生が明日決めると話したことは事実で、私が選ばれるかはまだ推測である',
          '先生が私を選んだことは事実で、明日決めるという発言は私の推測である',
          '先生は誰も選ばないと決め、私は発表を断ったことが事実である'], 0,
         '先生の発言として書かれているのは「明日決める」こと。自分が選ばれるという見込みは「私」の考えで、まだ決定した事実ではない。',
         ['先生のせりふと、「私」が思ったことを分けよう。', '「きっと」という見込みと、決定済みの事実は同じかな。'], '会話と心内の推測を区別する')
    edit('stretch-social-20261103:q4',
         '【架空の整備案】A案は1万2千円で2区画、B案は2万6千円で6区画を整備できる。同じ案を必要な回数だけ丸ごと使い、分割購入はしない。予算3万円以内で6区画以上にするには、どの方法が当てはまるか。',
         ['A案を2回使う', 'A案を3回使う', 'B案を1回使う'], 2,
         'A案2回は2万4千円で4区画なので区画数が不足。A案3回は6区画だが3万6千円で予算を超える。B案1回なら2万6千円で6区画となり、両方の条件を満たす。',
         ['予算と区画数を別々に確かめよう。', 'A案は2回なら4区画、3回なら3万6千円。B案はどうかな。'])
    edit('stretch-social-20261103:q5',
         '【架空の避難計画】70人が入る。定員24人の部屋は2部屋まで、定員15人の部屋は何部屋でも使える。必要な部屋数を最も少なくするには、全部で何部屋必要か。',
         ['3部屋', '4部屋', '5部屋'], 1,
         '3部屋の最大定員は24＋24＋15＝63人で不足する。4部屋なら24＋24＋15＋15＝78人まで入れるので、最小は4部屋。',
         ['3部屋で入れる人数を、いちばん多い組み合わせで考えよう。', '24人用2部屋と15人用1部屋では63人。もう1部屋加えると？'])

    def stretch(id, grade, skill, prompt, choices, answer, hints, explanation):
        question = {
            'id': id, 'subject': 'social', 'grade': grade, 'skill': skill, 'type': 'choice',
            'prompt': prompt, 'choices': choices, 'answer': answer, 'hints': hints, 'explanation': explanation,
            'status': 'prototype', 'auditStatus': 'independent_review_pending',
            'difficulty': 'stretch_design_not_empirically_calibrated',
        }
        return {'batch': 'stretch', 'subject': 'social', 'grade': grade,
                'source_file': 'dist/data/stretch-bank.json', 'question': question}

    items.extend([
        stretch('stretch-social-20261105:q6', 2, '地形図から経路の傾斜を比較する',
                '【架空の地形図の読み取り】同じ地形図で、山頂へ続くA道は等高線の間隔がせまく、B道は広い。なるべく緩やかな斜面の道を選びたい。この資料から選べるのは？',
                ['A道。等高線がせまいほど坂は緩やかだから', 'B道。等高線が広いほど坂は緩やかだから', 'どちらも同じ傾斜。山頂へ続く道だから'], 1,
                ['同じ地形図なら、隣り合う等高線の高さの差は同じだよ。', '同じ高さを、長い水平距離で上るのと短い距離で上るのでは、どちらが緩やかかな。'],
                '等高線の間隔が広いB道のほうが緩やかと読める。山頂が同じでも傾斜は同じとは限らない。この設問は傾斜の比較で、実際の道の安全性すべてを判断する資料ではない。'),
        stretch('stretch-social-20261105:q7', 2, '新旧の地図から土地利用の変化を読む',
                '【架空の新旧地図】同じ縮尺で同じ範囲を表した地図を比べた。昔の地図で田の記号が広がっていた場所に、現在の地図では住宅が描かれている。この二つの地図から直接読み取れるのは？',
                ['その場所の人口が、町のどの場所よりも多いこと',
                 '現在の住宅が、どれも同じ年に建てられたこと',
                 'その場所の土地利用が、田から住宅地へ変わったこと'], 2,
                ['同じ場所で、地図に描かれたものがどう変わったかな。', '土地の使い方は分かるけれど、人口や建物ができた年も載っているかな。'],
                '同じ場所の田の記号が住宅の表示に変わったことから、土地利用の変化を読み取れる。人口の多さの順位や各住宅の建築年は、この資料に示されていない。'),
    ])
    APP.mkdir(parents=True, exist_ok=True)
    write_json(APP / 'review_items.json', items)
    questions = [item['question'] for item in items]
    export_questions(APP, questions)
    changes = change_rows([item['question'] for item in previous], questions)
    write_csv(APP / 'change_map_app_round7.csv', changes)
    write_json(APP / 'sources.json', {
        'stretch-social-20261105:q6': {'sources': ['https://www.gsi.go.jp/common/000082924.pdf'],
                                      'provenance': 'Producer-created fictional route; contour rule checked against GSI'},
        'stretch-social-20261105:q7': {'sources': ['https://maps.gsi.go.jp/'],
                                      'provenance': 'Producer-created fictional maps described in text; no real regional change asserted'},
        'policy': {'furigana': 'none', 'japanese': '光村図書', 'geography': '帝国書院',
                   'history': '東京書籍', 'civics': '日本文教出版', 'edition': 'unconfirmed'},
    })
    return items


if __name__ == '__main__':
    social = make_social()
    app = make_app()
    print(encode({'social_questions': len(social), 'app_review_questions': len(app)}))
