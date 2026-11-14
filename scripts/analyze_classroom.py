"""Count question surfaces, verify exports, and describe a classroom-build delta.

Numeric masking is a screening aid. It does not count concepts or certify coverage.
Run after build_all25.py; reports are written beside the generated student HTML.
"""

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


SUBJECTS = {
    'japanese': '国語', 'math': '数学', 'english': '英語',
    'science': '理科', 'social': '社会',
}
CAUTION = (
    '正規化問題文数はNFKC化と空白除去後の表面上の種類数。'
    '数値マスク種類数は数字列（小数等を含む）を#に置換した問題文の種類数で、'
    '数値違い反復の偏りを探すための参考値。人名・語句違いは統合せず、'
    '年代・単位・問題の条件として重要な数字も統合する。'
    'いずれも学習内容数、理解の深さ、正答の正しさ、指導要領の収録率を表さない。'
)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prompt_key(prompt):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', prompt))


def numeric_mask(prompt):
    return re.sub(r'\d+(?:[.,]\d+)*', '#', prompt_key(prompt))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_runtime(runtime):
    dist = runtime / 'dist'
    catalog = read_json(dist / 'data/catalog.json')
    bank, unit_ids, packs = {}, {}, {}
    for unit in catalog['units']:
        ids = []
        for pack in unit['packs']:
            questions = read_json(dist / pack['file'])
            require(len(questions) == pack['count'], f"Pack count: {pack['id']}")
            packs[pack['file']] = questions
            for question in questions:
                qid = question['id']
                require(qid not in bank, f'Duplicate question ID: {qid}')
                require(question['unitId'] == unit['id'], f'Unit mismatch: {qid}')
                require(question['grade'] == unit['grade'], f'Grade mismatch: {qid}')
                require(question['subject'] == unit['subject'], f'Subject mismatch: {qid}')
                bank[qid] = question
                ids.append(qid)
        unit_ids[unit['id']] = ids
    return catalog, bank, unit_ids, packs


def answer_text(question):
    if question['type'] == 'choice':
        return question['choices'][question['answer']]
    if question['type'] == 'text':
        return ' / '.join(question['answers'])
    return str(question['answer'])


def verify_exports(runtime, catalog, bank, packs):
    rows = list(csv.DictReader((runtime / 'teacher_answers.csv').open(encoding='utf-8-sig', newline='')))
    require(len(rows) == len(bank), 'Teacher CSV row count differs from bank')
    require(len({row['ID'] for row in rows}) == len(rows), 'Duplicate teacher CSV IDs')
    require({row['ID'] for row in rows} == set(bank), 'Teacher CSV ID set differs from bank')
    titles = {unit['id']: unit['title'] for unit in catalog['units']}
    for row in rows:
        q = bank[row['ID']]
        expected = {
            '学年': str(q['grade']), '教科': SUBJECTS[q['subject']],
            '単元': titles[q['unitId']], '問題': q['prompt'],
            '選択肢': ' / '.join(q.get('choices', [])),
            '正答': answer_text(q), '解説': q['explanation'],
            '音声原稿': q.get('transcript', ''),
        }
        for field, value in expected.items():
            require(row[field] == value, f"Teacher CSV {field}: {q['id']}")
    html = (runtime / 'manabi_25.html').read_text(encoding='utf-8')
    match = re.search(r'const classroomAssets=([^\n]+);\n', html)
    require(match is not None, 'Student HTML has no embedded assets')
    embedded = json.loads(match[1])
    require(embedded['data']['data/catalog.json'] == catalog, 'Student HTML catalog differs')
    for name, data in packs.items():
        require(embedded['data'].get(name) == data, f'Student HTML pack differs: {name}')
    # Check the remaining embedded JSON as well, including supporting app data.
    json_files = sorted((runtime / 'dist/data').rglob('*.json'))
    for file in json_files:
        name = file.relative_to(runtime / 'dist').as_posix()
        require(embedded['data'].get(name) == read_json(file), f'Student HTML data differs: {name}')
    return {'teacher_rows_checked': len(rows), 'embedded_json_files_checked': len(json_files)}


def surface_counts(questions):
    questions = list(questions)
    return {
        'question_ids': len(questions),
        'normalized_prompts': len({prompt_key(q['prompt']) for q in questions}),
        'numeric_mask_prompts': len({numeric_mask(q['prompt']) for q in questions}),
        'prompts_with_digits': sum(bool(re.search(r'\d', prompt_key(q['prompt']))) for q in questions),
        'types': dict(sorted(Counter(q['type'] for q in questions).items())),
    }


def make_delta(current, previous):
    added = sorted(set(current) - set(previous))
    deleted = sorted(set(previous) - set(current))
    changes = []
    for qid in sorted(set(previous) & set(current)):
        before, after = previous[qid], current[qid]
        fields = {
            field: {'before': before.get(field), 'after': after.get(field)}
            for field in sorted(set(before) | set(after))
            if before.get(field) != after.get(field)
        }
        if fields:
            changes.append({'id': qid, 'fields': fields})
    return {
        'baseline_questions': len(previous), 'current_questions': len(current),
        'added_count': len(added), 'changed_count': len(changes), 'deleted_count': len(deleted),
        'unchanged_count': len(set(current) & set(previous)) - len(changes),
        'added_ids': added, 'deleted_ids': deleted, 'changed_questions': changes,
    }


def expect_repair(delta, bank, previous):
    expected_changes = {f'exam-section-093-all25:q{i:02}' for i in range(1, 6)}
    expected_additions = {f'{prefix}-{i:03}' for prefix in ('CR-SCI3', 'CR-MATH1', 'CR-ENG2') for i in range(1, 26)}
    require(len(previous) == 8698, 'Repair baseline must have 8,698 questions')
    require(set(delta['added_ids']) == expected_additions, 'Unexpected repair additions')
    require(not delta['deleted_ids'], 'Repair must not delete questions')
    require({row['id'] for row in delta['changed_questions']} == expected_changes,
            'Unexpected repair changes')
    for change in delta['changed_questions']:
        qid = change['id']
        before, after = previous[qid], bank[qid]
        require(set(change['fields']) <= {'prompt', 'choices', 'answer'}, f'Unexpected fields: {qid}')
        require(after['prompt'] == before['prompt'].replace('「3人の中で最も背が高い」', '「全生徒の中で最も背が高い」'),
                f'Unexpected translation repair: {qid}')
        require(sorted(before['choices']) == sorted(after['choices']), f'Options changed: {qid}')
        require(answer_text(before) == answer_text(after) == 'the tallest', f'Correct answer changed: {qid}')
    assignments = {
        'CR-SCI3': (3, 'science', 'repair-science-g3-data'),
        'CR-MATH1': (1, 'math', 'repair-math-g1-primes'),
        'CR-ENG2': (2, 'english', 'repair-english-g2-obligation'),
    }
    for qid in expected_additions:
        q = bank[qid]
        require((q['grade'], q['subject'], q['unitId']) == assignments[qid.rsplit('-', 1)[0]],
                f'Unexpected added question assignment: {qid}')


def expect_conjugation(delta, bank, previous):
    expected = {f'CR-JPN2-{i:03}' for i in range(1, 26)}
    require(len(previous) == 8773, 'Conjugation baseline must have 8,773 questions')
    require(set(delta['added_ids']) == expected, 'Unexpected conjugation additions')
    require(not delta['deleted_ids'] and not delta['changed_questions'],
            'The previous 8,773 questions must remain unchanged')
    for qid in expected:
        q = bank[qid]
        require((q['grade'], q['subject'], q['unitId']) ==
                (2, 'japanese', 'repair-japanese-g2-conjugation'),
                f'Unexpected conjugation assignment: {qid}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime_dir', type=Path)
    parser.add_argument('baseline_dir', type=Path)
    acceptance = parser.add_mutually_exclusive_group()
    acceptance.add_argument('--expect-repair', action='store_true', help='Require exactly the reviewed 75 additions and five translation fixes')
    acceptance.add_argument('--expect-conjugation', action='store_true', help='Require 25 conjugation additions and preserve all previous 8,773 questions')
    args = parser.parse_args()
    runtime, baseline = args.runtime_dir.resolve(), args.baseline_dir.resolve()
    catalog, bank, unit_ids, packs = load_runtime(runtime)
    _, previous, _, _ = load_runtime(baseline)
    exports = verify_exports(runtime, catalog, bank, packs)
    delta = make_delta(bank, previous)
    if args.expect_repair:
        expect_repair(delta, bank, previous)
    if args.expect_conjugation:
        expect_conjugation(delta, bank, previous)
    by_combination = []
    for grade in (1, 2, 3):
        for subject in SUBJECTS:
            questions = [q for q in bank.values() if q['grade'] == grade and q['subject'] == subject]
            by_combination.append({
                'grade': grade, 'subject': subject,
                'regular_units': sum(u['grade'] == grade and u['subject'] == subject for u in catalog['units']),
                'exam_sections': sum(s['grade'] == grade and s['subject'] == subject for s in catalog['examSections']),
                **surface_counts(questions),
            })
    report = {
        'caution_ja': CAUTION, 'normalization': 'NFKC then remove Unicode whitespace',
        'numeric_mask_regex': r'\d+(?:[.,]\d+)*',
        'all_questions': surface_counts(bank.values()),
        'by_grade_subject': by_combination,
        'exports_verified': exports,
        'repair_delta_acceptance': 'passed' if args.expect_repair else 'not requested',
        'conjugation_delta_acceptance': 'passed' if args.expect_conjugation else 'not requested',
    }
    with (runtime / 'unit_quality.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(['画面', '学年', '教科', '章', '単元', 'ID', '実ID数', '正規化問題文数',
                         '数値マスク問題文種類数_内容数ではない', '数字を含む問題文数', '選択式', '数値入力', '語句入力'])
        units = [('通常', u, unit_ids[u['id']]) for u in catalog['units']]
        units += [('定期テスト対策', s, s['ids']) for s in catalog['examSections']]
        for screen, unit, ids in units:
            require(len(ids) == len(set(ids)), f"Duplicate unit references: {unit['id']}")
            counts = surface_counts(bank[qid] for qid in ids)
            require(counts['normalized_prompts'] >= 25, f"Fewer than 25 distinct prompts: {unit['id']}")
            writer.writerow([screen, unit['grade'], SUBJECTS[unit['subject']], unit.get('chapter', ''),
                             unit['title'], unit['id'], counts['question_ids'], counts['normalized_prompts'],
                             counts['numeric_mask_prompts'], counts['prompts_with_digits'],
                             *[counts['types'].get(kind, 0) for kind in ('choice', 'number', 'text')]])
    write_json(runtime / 'quality.json', report)
    write_json(runtime / 'delta.json', delta)
    print(json.dumps({'all_questions': report['all_questions'], 'exports_verified': exports,
                      'added': delta['added_count'], 'changed': delta['changed_count'],
                      'deleted': delta['deleted_count'], 'repair_delta_acceptance': report['repair_delta_acceptance'],
                      'conjugation_delta_acceptance': report['conjugation_delta_acceptance']},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
