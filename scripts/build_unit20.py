"""Extend the classroom edition to twenty questions in every catalog unit."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import build_release_runtime_v2 as previous
from unit20 import english, japanese, math, science, social

ROOT = Path(__file__).resolve().parents[1]
GENERATORS = {'english': english, 'japanese': japanese, 'math': math, 'science': science, 'social': social}


def read_json(path):
    return json.loads(path.read_text())


def prompt_key(prompt):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', prompt))


def fill_units(out):
    dist = out / 'dist'
    catalog_path = dist / 'data/catalog.json'
    catalog = read_json(catalog_path)
    used = {prompt_key(q['prompt']) for unit in catalog['units'] for pack in unit['packs']
            for q in read_json(dist / pack['file'])}
    rows = []
    added = []
    by_cell = Counter()
    for unit in catalog['units']:
        prior = sum(p['count'] for p in unit['packs'])
        items = []
        unit_id = unit['id']
        subject = unit['subject']
        pack_id = f'{unit_id}-practice20'
        for index in range(160):
            if prior + len(items) >= 20:
                break
            item = GENERATORS[subject].generate(unit_id, index)
            key = prompt_key(item['prompt'])
            if key in used:
                continue
            used.add(key)
            item.update(id=f'{pack_id}:q{len(items)+1:02}', unitId=unit_id,
                        subject=subject, grade=unit['grade'], status='prototype')
            if 'transcript' in item:
                item['audio'] = f'data/audio/{pack_id}-q{len(items)+1:02}.mp3'
                previous.add_audio(dist / item['audio'], item['transcript'])
            items.append(item)
        if prior + len(items) < 20:
            raise ValueError(f'{unit_id}: only {prior+len(items)} distinct questions')
        if items:
            file = f'data/packs/{pack_id}.json'
            previous.write_json(dist / file, items)
            revision = hashlib.sha256((dist / file).read_bytes()).hexdigest()[:12]
            unit['packs'].append(dict(id=pack_id, file=file, revision=revision, count=len(items), randomized=False))
            if unit['status'] != 'prototype':
                unit['status'] = 'prototype'
        total = prior + len(items)
        rows.append(dict(id=unit_id, grade=unit['grade'], subject=previous.SUBJECTS[subject],
                         unit=unit['title'].replace('【試作】', ''), before=prior, added=len(items), total=total))
        by_cell[f"{subject}_g{unit['grade']}"] += total
        added.extend(items)
    previous.write_json(catalog_path, catalog)
    return catalog, rows, added, by_cell


def update_navigation(dist, unit_count, total):
    app = dist / 'app.js'
    js = app.read_text()
    old = 'if(a===\'demo\')startDemo();'
    assert js.count(old) == 1
    js = js.replace(old, old + "if(a==='practice20'){start('practice',b.dataset.unit,20);return}")
    old = '>5問練習する</button>'
    assert js.count(old) == 1
    js = js.replace(old, old + '<button class="secondary" data-action="practice20" data-unit="${u.id}">20問に挑戦</button>')
    js = js.replace("u.status==='prototype'?'試作教材':'確認済み教材'",
                    "u.status==='prototype'?'練習教材':'確認済み教材'")
    app.write_text(js)
    index = dist / 'index.html'
    html = index.read_text()
    html = html.replace('&amp;q=授業練習', '')
    html = html.replace('aria-label="学年別の授業練習"', 'aria-label="学年と教科を選ぶ"')
    html = re.sub(r'授業試用版・授業練習\d+問。', f'授業練習版。{unit_count}単元、通常問題{total:,}問。', html, count=1)
    index.write_text(html)


def csv_file(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    out = parser.parse_args().output.resolve()
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_release_runtime_v2.py'), str(out)], check=True)
    catalog, rows, added, by_cell = fill_units(out)
    total = sum(row['total'] for row in rows)
    update_navigation(out / 'dist', len(rows), total)
    csv_file(out / 'unit_counts.csv', rows)
    teacher = []
    for unit in catalog['units']:
        for pack in unit['packs']:
            for q in read_json(out / 'dist' / pack['file']):
                answer = q['choices'][q['answer']] if q['type'] == 'choice' else (
                    ' / '.join(q['answers']) if q['type'] == 'text' else str(q['answer']))
                teacher.append(dict(id=q['id'], grade=unit['grade'], subject=previous.SUBJECTS[unit['subject']],
                                    unit=unit['title'], prompt=q['prompt'], answer=answer,
                                    explanation=q['explanation'], audio_text=q.get('transcript', ''),
                                    added_in_unit20=q['id'].split(':')[0].endswith('-practice20')))
    csv_file(out / 'teacher_answers.csv', teacher)
    (out / 'manabi_20.html').write_text(previous.offline_html(out / 'dist'), encoding='utf-8')
    summary = dict(units=len(rows), total=total, added=len(added), minimum=min(row['total'] for row in rows),
                   maximum=max(row['total'] for row in rows), by_subject_grade=by_cell,
                   new_types=dict(Counter(q['type'] for q in added)), added_audio=sum('audio' in q for q in added))
    previous.write_json(out / 'unit20_summary.json', summary)
    manifest = read_json(out / 'source-manifest.json')
    manifest['unit20'] = summary
    manifest['draft_sha256'] = {str(f.relative_to(out)): hashlib.sha256(f.read_bytes()).hexdigest()
                                for f in sorted((out / 'dist').rglob('*')) if f.is_file()}
    previous.write_json(out / 'source-manifest.json', manifest)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
