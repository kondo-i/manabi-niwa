"""Independent read-back of social v3 and app-review v3, including historical drafts."""
import argparse
import tempfile
import collections
import csv
import difflib
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def normalized(text):
    return re.sub(r'[\s。、，．「」『』【】?？：:]', '', unicodedata.normalize('NFKC', text))


def verify_change_map(before, after, path):
    old = {question['id']: question for question in before}
    expected = []
    for question in after:
        previous = old.get(question['id'])
        if previous is None:
            expected.append((question['id'], 'add', '__item__', None, question))
            continue
        expected.extend((question['id'], 'modify', field, previous.get(field), question.get(field))
                        for field in dict.fromkeys([*previous, *question])
                        if previous.get(field) != question.get(field))
    actual = [(row['id'], row['operation'], row['field'], json.loads(row['before']), json.loads(row['after']))
              for row in rows(path)]
    assert actual == expected, str(path)
    assert len({(row[0], row[2]) for row in actual}) == len(actual)
    return actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="manabi-social-v3-"))
    output_dir.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append({'name': name, 'status': 'PASS'})

    social_folder = ROOT / 'data/social/v3'
    app_folder = ROOT / 'reports/app_review/v3'
    social = load(social_folder / 'questions.json')
    app = load(app_folder / 'questions.json')
    old_social = load(ROOT / 'data/social/v2/questions.json')
    old_app = [item['question'] for item in load(ROOT / 'reports/app_review/added_185_questions.json')]
    check('32 social and 187 app questions with unique IDs', len(social) == 32 and len(app) == 187
          and len({question['id'] for question in social + app}) == 219)
    for folder, questions in [(social_folder, social), (app_folder, app)]:
        back = [{key: json.loads(value) for key, value in row.items() if value != ''}
                for row in rows(folder / 'questions.csv')]
        check(str(folder.relative_to(ROOT)) + ' JSON/CSV full-field equality', back == questions)
        check(str(folder.relative_to(ROOT)) + ' choices and answer indices', all(
            len(question['choices']) == len(set(question['choices'])) == 3
            and type(question.get('correct_index', question.get('answer'))) is int
            and 0 <= question.get('correct_index', question.get('answer')) < 3 for question in questions))
        markdown = (folder / 'questions.md').read_text(encoding='utf-8')
        check(str(folder.relative_to(ROOT)) + ' Markdown content', all(
            question['id'] in markdown and question['prompt'] in markdown
            and question['explanation'] in markdown and all(choice in markdown for choice in question['choices'])
            for question in questions))
    check('Social answer strings match indices', all(q['choices'][q['correct_index']] == q['correct_answer'] for q in social))
    check('Social distractor notes match wrong choices and explanations', all(
        {note['choice'] for note in q['distractor_notes']} == set(q['choices']) - {q['correct_answer']}
        and all(note['choice'] in q['explanation'] and note['reason'] in q['explanation'] for note in q['distractor_notes'])
        for q in social))
    sources = load(social_folder / 'sources.json')['sources']
    check('Social source IDs resolve', all(all(id in sources for id in q['source_ids']) for q in social))
    check('Furigana absent and policy explicit', all(q['furigana_policy'] == 'none_by_user_request_20261105' for q in social)
          and all('<ruby' not in q['prompt'] + q['explanation'] for q in social + app))
    position_counts = dict(collections.Counter(q['correct_index'] + 1 for q in social))
    check('Social positions balanced within one question', max(position_counts.values()) - min(position_counts.values()) <= 1)
    sequences = [[q['correct_index'] for q in social]] + [
        [q['correct_index'] for q in social if q['field'] == field] for field in ['geography', 'history', 'civics']]
    check('No social answer-position periods of length 1 to 5', all(
        not any(all(sequence[index] == sequence[index % period] for index in range(len(sequence)))
                for period in range(1, 6)) for sequence in sequences))
    limited = [(q['id'], index, choice) for q in social for index, choice in enumerate(q['choices'])
               if re.search('だけ|必ず|すべて', choice)]
    check('No only/always/all cues in social choices', not limited)
    social_changes = verify_change_map(old_social, social, social_folder / 'change_map_v2_v3.csv')
    app_changes = verify_change_map(old_app, app, app_folder / 'change_map_app_round7.csv')
    check('Both change maps exact including full new-ID rows', True)
    by_id = {q['id']: q for q in social + app}
    check('HIS comparison moved to CIV explanation', '日本国憲法' not in by_id['SOC-HIS-010']['explanation']
          and '大日本帝国憲法' in by_id['SOC-CIV-001']['explanation'])
    check('CIV-008 all choices express rights', all(choice.endswith('権利がある') for choice in by_id['SOC-CIV-008']['choices']))
    check('Auxiliary quote and matched-usage task fixed', '「よう」' in by_id['japanese-g2-auxiliary-context-balance-001:q6']['prompt']
          and '同じ用法' in by_id['japanese-g2-auxiliary-context-balance-001:q4']['prompt']
          and '尊敬' not in by_id['japanese-g2-auxiliary-context-balance-001:q4']['prompt'])
    check('Honorific candidates revised in full', by_id['japanese-g2-honorific-context-balance-001:q1']['choices'] == ['いらっしゃる', '参る', '申す']
          and by_id['japanese-g2-honorific-context-balance-001:q9']['choices'] == ['おります', 'ございます', 'いらっしゃいます'])
    budgets = [(12000 * 2, 2 * 2), (12000 * 3, 2 * 3), (26000, 6)]
    check('New budget problem independently enumerated', [cost <= 30000 and plots >= 6 for cost, plots in budgets] == [False, False, True]
          and by_id['stretch-social-20261103:q4']['answer'] == 2)
    capacities = [(large + small, 24 * large + 15 * small)
                  for large in range(3) for small in range(6)]
    minimum = min(count for count, capacity in capacities if capacity >= 70)
    check('New room-capacity problem independently enumerated', minimum == 4
          and by_id['stretch-social-20261103:q5']['choices'][by_id['stretch-social-20261103:q5']['answer']] == '4部屋')
    check('Changed scale data independently calculated', 6 * 50000 / 100000 == 3
          and by_id['social-g1-geography-data-balance-001:q10']['choices'][0] == '3km')
    stretch = [q for q in app if q['id'].startswith('stretch-')]
    check('27 challenges have two hints and current audit flags', len(stretch) == 27
          and all(len(q['hints']) == 2 and q['auditStatus'] == 'independent_review_pending' for q in stretch))
    check('New non-calculation social tasks distinct in data',
          by_id['stretch-social-20261105:q6']['skill'] != by_id['stretch-social-20261105:q7']['skill']
          and by_id['SOC-GEO-011']['prompt'] != by_id['stretch-social-20261105:q6']['prompt'])

    # Include old versions with different IDs, rather than comparing only new text.
    candidates = social + app + old_social + old_app
    prompts = collections.defaultdict(list)
    for q in candidates:
        prompts[normalized(q['prompt'])].append(q['id'])
    exact_duplicates = [sorted(set(ids)) for ids in prompts.values() if len(set(ids)) > 1]
    check('No exact normalized prompt duplicates across IDs, including prior drafts', not exact_duplicates)
    current_ids = {q['id'] for q in social + app}
    old_by_id = {q['id']: q for q in old_social + old_app}
    changed_questions = [q for q in social + app if q['id'] not in old_by_id or q['prompt'] != old_by_id[q['id']]['prompt']]
    near = []
    for q in changed_questions:
        for other in candidates:
            if q['id'] == other['id']:
                continue
            left, right = normalized(q['prompt']), normalized(other['prompt'])
            similarity = difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
            if similarity >= 0.62:
                entry = {'id': q['id'], 'other_id': other['id'], 'similarity': round(similarity, 3),
                         'prompt': q['prompt'], 'other_prompt': other['prompt']}
                if entry not in near:
                    near.append(entry)
    (output_dir / 'duplicate_screening.json').write_text(json.dumps({
        'exact_prompt_duplicates': exact_duplicates, 'near_prompt_candidates': near,
        'scope': 'Current social32 + app187 against socialv2 + app185. Different-ID comparisons only.',
        'limit': 'Character similarity is a screening aid. Semantic/skill identity is not decided automatically.'
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    result = {
        'status': 'MECHANICAL_PASS_SEMANTIC_AND_TEXTBOOK_REAUDIT_PENDING',
        'social_questions': 32, 'social_added_ids': [q['id'] for q in social if q['id'] not in old_by_id],
        'social_changed_fields_and_added_rows': len(social_changes),
        'app_questions': 187, 'app_added_ids': [q['id'] for q in app if q['id'] not in old_by_id],
        'app_modified_ids': sorted({id for id, operation, field, before, after in app_changes if operation == 'modify'}),
        'app_changed_fields_and_added_rows': len(app_changes), 'social_positions': position_counts,
        'exact_normalized_duplicates': len(exact_duplicates), 'near_prompt_candidates': len(near),
        'semantic_duplicate_zero_verified': False,
        'textbook_edition_and_kanji_check': 'pending_edition_specific_grade_tables',
        'claude_csv_provided': False, 'checks': checks,
    }
    (output_dir / 'social_v3_verification_results.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
