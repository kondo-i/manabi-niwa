"""Apply round 7 audit and the user's natural-definition/no-furigana policy."""
import copy
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/v8'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def write_csv(path, rows, fields=None):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def main():
    original = json.loads((ROOT / 'data/v7/questions.json').read_text(encoding='utf-8'))
    questions = copy.deepcopy(original)
    meanings = [question for question in original if question['question_type'] == 'meaning']
    old_definitions = {question['target_word']: question['correct_answer'] for question in meanings}
    old_definitions['霧'] = '細かな水滴が空気中に浮かんで、視界が白くかすむこと'
    words_by_definition = {definition: word for word, definition in old_definitions.items()}
    noun_words = {word for word, definition in old_definitions.items() if definition.endswith('であること')}
    assert len(noun_words) == 99

    # Retain the referent for names of things, relations and parts of a text.
    definitions = {
        word: definition[:-5] + 'を指すこと' if word in noun_words else definition
        for word, definition in old_definitions.items()
    }
    # Emotion/action and quality entries are individually phrased.
    definitions.update({
        '不安': 'この先がどうなるか心配に思うこと',
        '期待': 'よい結果を楽しみに待つこと',
        '歓喜': '非常に強く喜ぶこと',
        '不満': '現状に満足できないと感じること',
        '卑劣': '正しさや思いやりを欠いた卑しいやり方をとること',
        '好奇心': '知らないものを知りたいと思うこと',
        '偏見': '十分な根拠なく特定の人や集団を決めつけて見ること',
        '主観': '自分の感じ方や考えを中心に物事を見ること',
        '疑念': '本当かどうかを疑うこと',
        '司法': '法律に基づいて争いを裁くこと',
        '立法': '社会の規則となる法律をつくること',
        '秩序': '物事が一定の規則に従って整っていること',
        '正確性': '誤りがなく確かな性質をもつこと',
        '再現性': '同じ条件や手順で繰り返したとき、同じ結果を得られる性質をもつこと',
        '透明性': '判断の過程や情報が外から分かる性質をもつこと',
        '轟音': '大きな音がとどろくこと',
        '硬質': '物が硬くしっかりした性質をもつこと',
        '柔軟': '曲げたり考えを変えたりできる性質をもつこと',
        '憂鬱': '気が晴れず沈んだ気持ちになること',
        '絶体絶命': '逃れる方法がないほど追い詰められること',
        '応急': '急場をしのぐために一時的な処置をすること',
    })
    # Every list retains the correct index. The log stores named word changes.
    replacement_words = {
        'JVQ-124-02-M': ['伝達', '推敲', '明文化'],
        'JVQ-044-02-M': ['傾向', '主観', '仮説'],
        'JVQ-082-03-M': ['静寂', '轟音', 'ささやき'],
        'JVQ-090-03-M': ['柔軟', '粗い', '硬質'],
        'JVQ-090-04-M': ['硬質', '柔軟', '滑らか'],
        'JVQ-108-01-M': ['前途多難', '絶体絶命', '五里霧中'],
        'JVQ-015-02-M': ['傲慢', '誠実', '謙虚'],
        'JVQ-059-03-M': ['国際', '地域', '国家'],
        'JVQ-059-04-M': ['国家', '地域', '地球規模'],
        'JVQ-111-01-M': ['隠蔽', '虚偽', '伝達'],
        'JVQ-113-04-M': ['論破', 'すり替え', '詭弁'],
        'JVQ-114-04-M': ['拡散', '続報', '誤報'],
        'JVQ-060-03-M': ['事故', '紛争', '災害'],
    }
    domains = {
        'JVQ-124-02-M': '文章・情報を形にして伝える行為。推敲は文章を練り直す行為で、文章にして示す明文化とは異なる。',
        'JVQ-044-02-M': '物事の捉え方と探究。仮説は検証前の仮の説明で、自分の感じ方を中心に見る主観とは異なる。',
        'JVQ-082-03-M': '音の大きさ・静けさ。静寂は音がなく静か、ささやきは小声、轟音は大きな音。',
        'JVQ-090-03-M': '物の性質。粗いはきめ、柔軟は曲げられる性質、硬質は硬くしっかりした性質。',
        'JVQ-090-04-M': '物や動きの性質。滑らかは表面や動きのなめらかさ、硬質は硬さ、柔軟は曲げられる性質。',
        'JVQ-108-01-M': '困難に関する四字熟語。前途多難は将来の困難、五里霧中は方針が見えないこと、絶体絶命は逃れようがない危機。',
        'JVQ-015-02-M': '対人態度。傲慢は自己を偉いと思って見下すこと、誠実はごまかさず向き合うこと、謙虚は偉いと思わず学ぶこと。',
        'JVQ-059-03-M': '社会の空間的なまとまり。国際は国と国の間の関係、地域は区切られた場所、国家は政治的なまとまり。',
        'JVQ-059-04-M': '社会の空間的なまとまり。地球規模は地球全体に及ぶ範囲、国家は政治的まとまり、地域は区切られた場所。',
        'JVQ-111-01-M': '情報の真偽と扱い。虚偽はうその内容、隠蔽は隠す行為、伝達は情報を届ける行為。',
        'JVQ-113-04-M': '議論の操作。詭弁は不正確な議論、論破は論理で誤りを退ける行為、すり替えは論点を置き換える行為。',
        'JVQ-114-04-M': '情報の伝わり方。続報はその後を知らせる報道、誤報は事実と異なる報道、拡散は広く伝わること。',
        'JVQ-060-03-M': '被害を伴う出来事。災害は自然現象などの被害、事故は思いがけない損害、紛争は利害などによる争い。',
    }
    replacement_log = []
    for old, question in zip(original, questions):
        question['furigana_policy'] = 'none_by_user_request_20261105'
        question['grade_policy'] = 'mitsumura_alignment_pending_edition_and_grade_table'
        if question['question_type'] == 'meaning':
            old_words = [words_by_definition[definition] for definition in old['choices']]
            words = replacement_words.get(question['id'], old_words)
            assert words[question['correct_index']] == question['target_word'], question['id']
            for index, (old_word, word) in enumerate(zip(old_words, words)):
                if old_word != word:
                    assert index != question['correct_index']
                    replacement_log.append({
                        'id': question['id'], 'choice_number': index + 1,
                        'before_word': old_word, 'after_word': word,
                        'target_word': question['target_word'], 'semantic_basis': domains[question['id']],
                        'origin': 'user_round7_text_and_producer_selection_without_CSV',
                    })
            question['choices'] = [definitions[word] for word in words]
            question['correct_answer'] = definitions[question['target_word']]
            if question['choices'] != old['choices']:
                wrong = [word for index, word in enumerate(words) if index != question['correct_index']]
                question['explanation'] = (
                    f'「{question["target_word"]}」は{question["correct_answer"]}。'
                    f'一方、「{wrong[0]}」は{definitions[wrong[0]]}。'
                    f'また、「{wrong[1]}」は{definitions[wrong[1]]}。'
                    'それぞれの意味の中心を比べて区別しよう。'
                )
        elif question['question_type'] == 'context':
            for word in question['choices']:
                question['explanation'] = question['explanation'].replace(
                    f'「{word}」は{old_definitions[word]}', f'「{word}」は{definitions[word]}'
                )

    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / 'questions.json', questions)
    fields = list(dict.fromkeys(field for question in questions for field in question))
    write_csv(OUT / 'questions.csv', [
        {field: encode(question[field]) if field in question else '' for field in fields}
        for question in questions
    ], fields)
    changes = []
    for old, question in zip(original, questions):
        for field in question:
            if old[field] != question[field]:
                changes.append({
                    'id': question['id'], 'field': field, 'before': encode(old[field]),
                    'after': encode(question[field]),
                    'reason': 'user_policy' if field.endswith('_policy') else 'round7_definition_or_distractor_revision',
                })
    write_csv(OUT / 'change_map_v7_v8.csv', changes)
    definition_changes = []
    for word, definition in definitions.items():
        if definition != old_definitions[word]:
            style = 'referent' if definition.endswith('を指すこと') else 'quality' if definition.endswith('をもつこと') else 'action_or_state'
            definition_changes.append({'word': word, 'before': old_definitions[word], 'after': definition, 'style': style})
    write_csv(OUT / 'definition_changes.csv', definition_changes)
    write_csv(OUT / 'distractor_replacements.csv', replacement_log)
    write_csv(OUT / 'targeted_semantic_review.csv', [
        {'id': id, 'domain_and_distinction': reason, 'status': 'producer_review_independent_reaudit_pending'}
        for id, reason in domains.items()
    ])
    write_json(OUT / 'canonical_definitions.json', definitions)
    write_json(OUT / 'textbook_policy.json', {
        'decided_on': '2026-11-05', 'japanese_publisher': '光村図書',
        'furigana': 'none', 'grade_and_kanji_policy': 'align_to_selected_textbook',
        'edition': None, 'edition_status': 'publisher_confirmed_edition_unspecified',
        'grade_changes': 0, 'kanji_allocation_check': 'pending_grade_specific_textbook_tables',
    })
    print(encode({'questions': len(questions), 'definitions_changed': len(definition_changes),
                  'distractor_choices_replaced': len(replacement_log), 'changed_fields': len(changes)}))


if __name__ == '__main__':
    main()
