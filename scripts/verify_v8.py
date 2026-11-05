"""Read back exported data and recompute all linked changes independently."""
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/v8'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    old = read_json(ROOT / 'data/v7/questions.json')
    current = read_json(FOLDER / 'questions.json')
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append({'name': name, 'status': 'PASS'})

    check('1040 unique IDs, unchanged order', len(current) == len({q['id'] for q in current}) == 1040
          and [q['id'] for q in current] == [q['id'] for q in old])
    back = [{key: json.loads(value) for key, value in row.items() if value != ''}
            for row in read_csv(FOLDER / 'questions.csv')]
    check('CSV all fields and types reconstruct exactly', back == current)
    check('Three distinct choices and answer consistency', all(
        len(q['choices']) == len(set(q['choices'])) == 3
        and type(q['correct_index']) is int and 0 <= q['correct_index'] < 3
        and q['choices'][q['correct_index']] == q['correct_answer'] for q in current))
    groups = {kind: [q for q in current if q['question_type'] == kind]
              for kind in ['meaning', 'context', 'logical_reading']}
    check('500 meanings, 500 contexts, 40 readings', [len(q) for q in groups.values()] == [500, 500, 40])
    definitions = {q['target_word']: q['correct_answer'] for q in groups['meaning']}
    definitions['霧'] = '細かな水滴が空気中に浮かんで、視界が白くかすむこと'
    names = {definition: word for word, definition in definitions.items()}
    check('501 canonical definitions unique and match manifest',
          len(names) == 501 and definitions == read_json(FOLDER / 'canonical_definitions.json'))
    check('No であること endings, no mixed types, 1500 こと endings', all(
        definition.endswith('こと') and not definition.endswith('であること')
        for q in groups['meaning'] for definition in q['choices']))
    check('All M current word names and definitions in explanation', all(
        definition in q['explanation'] and f'「{names[definition]}」' in q['explanation']
        for q in groups['meaning'] for definition in q['choices']))
    check('All C word names and current definitions linked exactly', all(
        f'「{word}」は{definitions[word]}' in q['explanation']
        for q in groups['context'] for word in q['choices']))
    old_definitions = {q['target_word']: q['correct_answer'] for q in old if q['question_type'] == 'meaning'}
    changed_definitions = {word for word, definition in old_definitions.items() if definitions[word] != definition}
    expected_words = {word for word, definition in old_definitions.items() if definition.endswith('であること')}
    check('Exactly 99 old noun definitions changed', changed_definitions == expected_words and len(expected_words) == 99)
    definition_rows = read_csv(FOLDER / 'definition_changes.csv')
    check('Definition log exact old and new values', len(definition_rows) == 99
          and {row['word'] for row in definition_rows} == changed_definitions
          and all(row['before'] == old_definitions[row['word']] and row['after'] == definitions[row['word']]
                  for row in definition_rows))
    by_id = {q['id']: q for q in current}
    old_by_id = {q['id']: q for q in old}
    replacements = read_csv(FOLDER / 'distractor_replacements.csv')
    check('Named replacements match old/new actual wrong choices', len(replacements) == 21
          and len({(row['id'], row['choice_number']) for row in replacements}) == 21
          and all(int(row['choice_number']) - 1 != by_id[row['id']]['correct_index']
                  and by_id[row['id']]['choices'][int(row['choice_number']) - 1] == definitions[row['after_word']]
                  and old_by_id[row['id']]['choices'][int(row['choice_number']) - 1] == old_definitions[row['before_word']]
                  for row in replacements))
    review_ids = {row['id'] for row in read_csv(FOLDER / 'targeted_semantic_review.csv')}
    check('All 13 audit targets have named semantic review records', len(review_ids) == 13
          and {row['id'] for row in replacements} == review_ids)
    requested = {
        'JVQ-124-02-M': {'推敲'}, 'JVQ-044-02-M': {'仮説'},
        'JVQ-082-03-M': {'静寂', 'ささやき'}, 'JVQ-090-03-M': {'粗い'},
        'JVQ-090-04-M': {'滑らか'}, 'JVQ-108-01-M': {'前途多難', '五里霧中'},
    }
    check('All six P2 requested word replacements present', all(
        definitions[word] in by_id[id]['choices'] for id, words in requested.items() for word in words))
    protected = ['id', 'grade', 'passage', 'prompt', 'correct_index', 'review_status', 'claude_audit', 'release_status']
    check('Protected content and historic audit flags preserved', all(
        before.get(key) == after.get(key) for before, after in zip(old, current) for key in protected))
    check('No furigana and textbook policy recorded', all(
        q['furigana_policy'] == 'none_by_user_request_20261105'
        and q['grade_policy'] == 'mitsumura_alignment_pending_edition_and_grade_table'
        and '<ruby' not in q['prompt'] + q['explanation'] for q in current))
    actual = {(after['id'], key, json.dumps(before[key], ensure_ascii=False), json.dumps(after[key], ensure_ascii=False))
              for before, after in zip(old, current) for key in after if before[key] != after[key]}
    change_rows = read_csv(FOLDER / 'change_map_v7_v8.csv')
    listed = {(row['id'], row['field'], json.dumps(json.loads(row['before']), ensure_ascii=False),
               json.dumps(json.loads(row['after']), ensure_ascii=False)) for row in change_rows}
    check('Change map exact IDs, fields, before and after, no extras', actual == listed and len(listed) == len(change_rows))
    content_fields = {'choices', 'correct_answer', 'explanation'}
    content_changes = [row for row in change_rows if row['field'] in content_fields]
    linked_ids = sorted({q['id'] for q in groups['meaning'] if any(
        definition in q['choices'] for word, definition in definitions.items() if word in changed_definitions)}
        | {q['id'] for q in groups['context'] if any(word in changed_definitions for word in q['choices'])})
    style_outliers = []
    for question in groups['meaning']:
        styles = ['referent' if value.endswith('を指すこと') else 'quality' if value.endswith('をもつこと') else 'action_or_state'
                  for value in question['choices']]
        if len(set(styles)) == 2:
            unique = next(index for index, style in enumerate(styles) if styles.count(style) == 1)
            style_outliers.append({'id': question['id'], 'unique_choice_number': unique + 1,
                                   'unique_is_correct': unique == question['correct_index']})
    result = {
        'status': 'MECHANICAL_PASS_INDEPENDENT_SEMANTIC_REVIEW_PENDING',
        'questions': 1040, 'changed_questions': len({row['id'] for row in change_rows}),
        'changed_fields': len(change_rows), 'content_changed_questions': len({row['id'] for row in content_changes}),
        'content_changed_fields': len(content_changes), 'definition_changes': 99,
        'distractor_choices_replaced': len(replacements), 'ending_mixed_questions': 0,
        'natural_style_outliers': style_outliers,
        'natural_style_outlier_correct_count': sum(row['unique_is_correct'] for row in style_outliers),
        'linked_definition_ids': linked_ids, 'targeted_ids': sorted(review_ids),
        'content_changed_by_type': dict(collections.Counter(by_id[id]['question_type']
                                      for id in sorted({row['id'] for row in content_changes}))),
        'semantic_domain_limit': '13 targeted items reviewed by producer; broad semantic domain equality is not machine-proven',
        'textbook_kanji_allocation': 'publisher_confirmed_grade_specific_edition_tables_pending',
        'claude_csv_provided': False, 'checks': checks,
        'sha256_lf': {path.name: hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                      for path in sorted(FOLDER.iterdir()) if path.is_file()},
    }
    (ROOT / 'reports/v8_verification_results.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ['checks', 'sha256_lf', 'linked_definition_ids', 'targeted_ids']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
