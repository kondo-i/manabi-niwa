"""Unify the bounded source/body audits and recalculate final section counts."""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/coverage_repair'
BASE = 'e537d753465c00ab5cf43bf060661094dd608055'
SUBJECTS = dict(japanese='国語', math='数学', english='英語', science='理科', social='社会')

def key(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))

def read_rows(name):
    with (REPORT / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main(runtime):
    catalog = json.loads((runtime / 'dist/data/catalog.json').read_text())
    bank = {q['id']: q for u in catalog['units'] for p in u['packs']
            for q in json.loads((runtime / 'dist' / p['file']).read_text())}
    sections = {s['id']: s for s in catalog['examSections']}
    rows = []
    def add(grade, subject, content, source, location, ids, units, base_count,
            base_prompts, body_count, evidence, limitation, gap, target, next_file, origin):
        new_id = 'repair-japanese-g2-conjugation'
        if str(grade) == '2' and subject == '国語' and content.startswith('用言の活用') and new_id in sections:
            ids = units = new_id
            location = '文科解説 第2学年 知識及び技能(1)オ（印刷p78／PDF p82） ; 光村R7中2計画PDF p20 文法2 用言の活用'
            body_count = 25
            evidence = ';'.join(sections[new_id]['ids'])
            limitation = '追加25問の全設問・全選択肢・正答・解説を作問者と独立担当が確認'
            gap = '固定比較元の不足を今回25問で補強。自由記述による活用表完成、学校固有のページ対応は未確認'
            target = '今回25問追加（本小単元のID不足0）。内容の完全収録を示すものではない'
            next_file = 'data/coverage_repair/japanese_conjugation.json'
            origin = 'reports/continuation_japanese/author_review.md ; independent_review.md'
        improvements = {
            (3, '理科', '水圧と浮力'): ('repair-science-g3-buoyancy', 'science_buoyancy.json', 'buoyancy_author.md'),
            (2, '数学', '箱ひげ図の表示・二群比較'): ('repair-math-g2-boxplots', 'math_boxplots.json', 'boxplots_author.md'),
        }
        improved = improvements.get((int(grade), subject, content))
        if improved and improved[0] in sections:
            ids = units = improved[0]
            body_count = 25
            evidence = ';'.join(sections[ids]['ids'])
            limitation = '今回追加25問を図・全選択肢・正答・解説まで作問者と独立担当が確認'
            gap = '固定比較元の不足を今回25問で補強。自由記述や学校固有のページ対応は未確認'
            target = '今回25問追加（本小単元のID不足0）。全内容の充足率ではない'
            next_file = 'data/coverage_repair/' + improved[1]
            origin = 'reports/publication_20261114/' + improved[2]
        allowed = {new_id} | {x[0] for x in improvements.values()}
        if 'repair-' in ids and ids not in allowed: return  # Previous additions are listed once below.
        known = [x for x in re.split(r'[;,\s]+', ids) if x in sections]
        final_ids = {qid for sid in known for qid in sections[sid]['ids']}
        rows.append(dict(比較元SHA=BASE, 学年=str(grade), 教科=subject, 学習内容=content,
                         根拠資料URL=source, 参照箇所=location, 対応小単元ID=ids,
                         通常単元ID=units, 比較元ID数=base_count, 比較元正規化問題文数=base_prompts,
                         最終版ID数=len(final_ids), 最終版正規化問題文数=len({key(bank[x]['prompt']) for x in final_ids}),
                         本文確認数=body_count, 確認問題ID=evidence, 確認の範囲=limitation,
                         不足または限界=gap, 不足問数または追加目標=target, 次に触るファイル=next_file, 元監査表=origin))
    for r in read_rows('language_coverage.csv'):
        add(r['grade'], SUBJECTS[r['subject']], r['learning_content'], r['source_url']+' ; '+r['annual_plan_url'],
            r['source_location']+' ; '+r['annual_plan_location'], r['section_ids'], r['normal_unit_ids'],
            r['registered_question_ids'], r['distinct_prompts_nfkc'], '抜粋・生成コード参照（元表確認ID参照）',
            r['evidence_question_ids'], r['judgement'], r['gap_or_limit'], r['minimum_questions_to_add'], r['next_file'], 'language_coverage.csv')
    for r in read_rows('social_math_coverage.csv'):
        add(r['学年'], r['教科'], r['学習内容'], r['根拠資料URL']+' ; '+r['学習指導要領URL'],
            r['参照箇所']+' ; '+r['指導要領参照箇所'], r['対応する定期テスト単元IDまたは候補'], r['通常単元ID'],
            r['実出題ID数'], r['正規化問題文数'], r['本文確認数'], r['確認問題ID'], r['判定'],
            r['未収録または不足の内容'], r['不足問数'], r['次に触るファイル'], 'social_math_coverage.csv')
    for r in read_rows('science_coverage.csv'):
        add(r['学年'], r['教科'], r['学習内容'], r['公開指導計画URL']+' ; '+r['指導要領URL'], r['根拠参照箇所'],
            r['定期テスト単元ID'], r['通常単元ID'], r['登録実出題数'], r['正規化問題文数'], r['本文確認数'],
            r['本文確認ID'], r['確認の範囲'], r['未収録または不足の内容'], r['不足問数または追加目標'], r['次に触るファイル'], 'science_coverage.csv')
    for sid, filename, note in [
        ('repair-math-g1-primes', 'math_primes.json', '定義・手順・誤手順・因数の活用'),
        ('repair-english-g2-obligation', 'english_obligation.json', '義務・禁止・不必要・疑問文・案内の複合条件'),
        ('repair-science-g3-data', 'science_material.json', '運動・仕事・エネルギー・イオン・天体の学習用資料')]:
        s = sections[sid]
        source_row = next(r for r in rows if r['教科'] == SUBJECTS[s['subject']] and r['学年'] == str(s['grade']))
        rows.append(dict(比較元SHA=BASE, 学年=str(s['grade']), 教科=SUBJECTS[s['subject']], 学習内容=s['title'],
                         根拠資料URL=source_row['根拠資料URL'], 参照箇所='各教科の監査メモ・新規単元の根拠節を参照',
                         対応小単元ID=sid, 通常単元ID=sid, 比較元ID数=0, 比較元正規化問題文数=0,
                         最終版ID数=len(s['ids']), 最終版正規化問題文数=len({key(bank[x]['prompt']) for x in s['ids']}),
                         本文確認数=25, 確認問題ID=';'.join(s['ids']), 確認の範囲='追加25問は作問者・独立担当が全文確認。'+note,
                         不足または限界='自由記述・実験操作の技能評価、学校固有のページ対応は未確認',
                         不足問数または追加目標='今回25問追加（本単元のID不足0）', 次に触るファイル='data/coverage_repair/'+filename,
                         元監査表='追加25問の独立監査メモ'))
    covered = {x for r in rows for x in re.split(r'[;,\s]+', r['対応小単元ID']) if x in sections}
    assert covered == set(sections), 'Missing section mapping: '+str(set(sections)-covered)
    assert {(int(r['学年']),r['教科']) for r in rows} == {(g,s) for g in (1,2,3) for s in SUBJECTS.values()}
    out = runtime / 'coverage_matrix.csv'
    with out.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = dict(rows=len(rows), mapped_registered_sections=len(covered), grade_subject_combinations=15,
                  caution='範囲照合の初回記録。全問監査・指導要領の全内容収録率ではない。関連内容は別小単元と共有する場合がある。')
    (runtime / 'coverage_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__ == '__main__': main(Path(sys.argv[1]).resolve())
