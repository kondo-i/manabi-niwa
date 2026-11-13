"""Build the classroom draft and a single-file offline edition."""
import argparse
import base64
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/expansion/v2'
SUBJECTS = {'japanese': '国語', 'math': '数学', 'english': '英語', 'science': '理科', 'social': '社会'}
NAMES = {'1': '中1', '2': '中2', '3': '中3'}


def write_json(file, value):
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_units():
    units = {}
    for subject in SUBJECTS:
        for line_no, line in enumerate((DATA / f'{subject}.txt').read_text().splitlines(), 1):
            if not line or line.startswith('//'):
                continue
            if line.startswith('@'):
                unit_subject, grade, topic, title = line[1:].split('|')
                assert unit_subject == subject and grade in NAMES
                unit_id = f'class-{subject}-g{grade}-{topic}'
                assert unit_id not in units
                units[unit_id] = (subject, int(grade), topic, title, [])
                items = units[unit_id][-1]
                continue
            parts = [part.strip().replace(r'\n', '\n') for part in line.split('|')]
            assert len(parts) >= 3 and all(parts), (subject, line_no)
            prompt, answer, *rest = parts
            question_id = f'{unit_id}-pack:q{len(items) + 1:02}'
            question = {'id': question_id, 'subject': subject, 'grade': int(grade),
                        'unitId': unit_id, 'status': 'prototype', 'prompt': prompt}
            if answer.startswith(('=', '#')):
                assert len(rest) == 1, (subject, line_no)
                if answer.startswith('#'):
                    question.update(type='number', answer=float(answer[1:]), tolerance=1e-9)
                else:
                    question.update(type='text', answers=answer[1:].split('/'))
                    if subject == 'english':
                        question['caseInsensitive'] = True
            else:
                assert len(rest) == 3, (subject, line_no)
                choices = [answer, *rest[:2]]
                assert len(set(choices)) == 3
                shift = (len(items) + int(grade)) % 3
                question.update(type='choice', choices=choices[shift:] + choices[:shift], answer=(-shift) % 3)
            explanation, _, transcript = rest[-1].partition('~')
            question['explanation'] = explanation
            assert bool(transcript) == (topic == 'listening'), (subject, line_no)
            if transcript:
                question.update(audio=f'data/audio/{question_id.replace(":", "-")}.mp3',
                                transcript=transcript)
            items.append(question)
    assert all(len(info[-1]) >= 5 for info in units.values())
    return units


def add_audio(file, transcript):
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / 'line.txt'
        source.write_text(transcript, encoding='ascii')
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        f'flite=textfile={source}:voice=slt', '-af', 'atempo=0.92',
                        '-codec:a', 'libmp3lame', '-b:a', '32k', str(file)], check=True)


def add_classroom_units(out, units):
    catalog_file = out / 'dist/data/catalog.json'
    catalog = json.loads(catalog_file.read_text())
    (out / 'dist/data/audio').mkdir()
    existing_ids = {unit['id'] for unit in catalog['units']}
    for unit_id, (subject, grade, topic, title, questions) in units.items():
        assert unit_id not in existing_ids
        pack_id = unit_id + '-pack'
        file = f'data/packs/{pack_id}.json'
        write_json(out / 'dist' / file, questions)
        for item in questions:
            if item.get('audio'):
                add_audio(out / 'dist' / item['audio'], item['transcript'])
        revision = hashlib.sha256((out / 'dist' / file).read_bytes()).hexdigest()[:12]
        catalog['units'].append({
            'id': unit_id, 'subject': subject, 'grade': grade, 'title': title,
            'description': '授業練習。聞き取りは音声を再生して解答します。' if topic == 'listening' else '授業練習',
            'status': 'prototype',
            'packs': [{'id': pack_id, 'file': file, 'revision': revision,
                       'count': len(questions), 'randomized': False}]
        })
    write_json(catalog_file, catalog)
    return catalog


def update_interface(dist, count):
    app = dist / 'app.js'
    js = app.read_text()
    marker = '<h1 class="question">${esc(q.prompt)}</h1>'
    assert js.count(marker) == 1
    js = js.replace(marker, marker + '${q.audio?\x60<div class="listening"><audio controls preload="none" src="${esc(window.ClassroomAudio?.[q.audio]||q.audio)}" aria-label="英語の聞き取り音声"></audio></div>\x60:\'\'}')
    marker = '<p>${esc(q.explanation)}</p>'
    assert js.count(marker) == 1
    js = js.replace(marker, marker + "${q.transcript?\x60<p lang=\"en\">${esc(q.transcript)}</p>\x60:''}")
    app.write_text(js)
    links = []
    for grade, label in NAMES.items():
        subjects = ' '.join(f'<a href="?page=subjects&amp;subject={subject}&amp;grade={grade}&amp;q=授業練習">{name}</a>'
                            for subject, name in SUBJECTS.items())
        links.append(f'<details><summary>{label}の練習</summary><div>{subjects}</div></details>')
    nav = '<nav class="classroom-nav" aria-label="学年別の授業練習">' + ''.join(links) + '</nav>'
    index = dist / 'index.html'
    html = index.read_text()
    html = re.sub(r'<body><div[^>]+>制作確認用・未公開[^<]+</div>', '<body>', html, count=1)
    html = html.replace('</header>', '</header>' + nav, 1)
    html = re.sub(r'<footer>制作確認用：[^<]+', f'<footer>授業試用版・授業練習{count}問。', html, count=1)
    html = html.replace('<body>', '<style>.classroom-nav{display:flex;gap:.6rem;flex-wrap:wrap;padding:.6rem 1rem;background:#e9f2e9}.classroom-nav details{background:#fff;border-radius:10px;padding:.45rem .7rem}.classroom-nav summary{cursor:pointer;font-weight:700}.classroom-nav a{display:inline-block;color:#235d48;padding:.3rem .5rem}.question{white-space:pre-line}.listening audio{width:min(100%,340px);margin:.5rem 0}.answer{overflow-wrap:anywhere}</style><body>', 1)
    index.write_text(html)


def offline_html(dist):
    """Bundle known local resources, with the same app entry point and grading."""
    html = (dist / 'index.html').read_text()
    html = re.sub(r'<link rel="stylesheet" href="([^"?]+)\?[^"]+">',
                  lambda m: '<style>' + (dist / m[1]).read_text() + '</style>', html)
    data = {p.relative_to(dist).as_posix(): json.loads(p.read_text()) for p in (dist / 'data').rglob('*.json')}
    audio = {p.relative_to(dist).as_posix(): 'data:audio/mpeg;base64,' + base64.b64encode(p.read_bytes()).decode()
             for p in (dist / 'data/audio').glob('*.mp3')}
    figures = {p.relative_to(dist).as_posix(): 'data:image/svg+xml;base64,' + base64.b64encode(p.read_bytes()).decode()
               for p in (dist / 'data').rglob('*.svg')}
    assets = json.dumps({'data': data, 'audio': audio, 'figures': figures}, ensure_ascii=False).replace('<', '\\u003c')
    bootstrap = '<script>const classroomAssets=' + assets + """;
window.ClassroomAudio=classroomAssets.audio;
window.ClassroomFigures=classroomAssets.figures;
const classroomFetch=window.fetch.bind(window);
window.fetch=async (input,options)=>{
  if(typeof input==='string'){
    const key=input.split('?')[0];
    if(Object.hasOwn(classroomAssets.data,key)){
      return new Response(JSON.stringify(classroomAssets.data[key]),{headers:{'Content-Type':'application/json'}});
    }
  }
  return classroomFetch(input,options);
};
</script>"""
    first = html.index('<script src=')
    html = html[:first] + bootstrap + html[first:]
    html = html.replace('href="?page=subjects&amp;', 'href="#?page=subjects&amp;')
    return re.sub(r'<script src="([^"?]+)\?[^"]+"></script>',
                  lambda m: '<script>' + inline_script(dist, m[1]) + '</script>', html)


def inline_script(dist, name):
    js = (dist / name).read_text()
    if name == 'app.js':
        js = js.replace("window.location?.search||''", "window.location.hash.slice(1)")
        js = js.replace("Routing.url(routeState()))", "'#'+Routing.url(routeState()))")
        js = js.replace("?.('popstate',", "?.('hashchange',")
        js = js.replace('esc(q.figure.src)', 'esc(window.ClassroomFigures?.[q.figure.src]||q.figure.src)')
        js = js.replace("crypto.randomUUID?crypto.randomUUID()", "globalThis.crypto?.randomUUID?crypto.randomUUID()")
    return js.replace('</script', r'<\/script')


def write_teacher_index(out, units):
    columns = ['id', 'subject', 'grade', 'unit', 'prompt', 'answer', 'explanation', 'audio_text']
    with (out / 'teacher_answers.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for subject, grade, topic, title, questions in units.values():
            for q in questions:
                answer = q['choices'][q['answer']] if q['type'] == 'choice' else ' / '.join(q['answers']) if q['type'] == 'text' else f"{q['answer']:g}"
                writer.writerow(dict(id=q['id'], subject=SUBJECTS[subject], grade=grade, unit=title,
                                     prompt=q['prompt'], answer=answer, explanation=q['explanation'],
                                     audio_text=q.get('transcript', '')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    out = parser.parse_args().output.resolve()
    units = read_units()
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_release_runtime_v1.py'), str(out)], check=True)
    catalog = add_classroom_units(out, units)
    questions = [q for info in units.values() for q in info[-1]]
    update_interface(out / 'dist', len(questions))
    (out / 'manabi_classroom.html').write_text(offline_html(out / 'dist'), encoding='utf-8')
    write_teacher_index(out, units)
    manifest_file = out / 'source-manifest.json'
    manifest = json.loads(manifest_file.read_text())
    manifest['classroom'] = {'questions': len(questions), 'units': len(units),
                             'audio': sum('audio' in q for q in questions),
                             'by_subject_grade': dict(Counter(f"{q['subject']}_g{q['grade']}" for q in questions)),
                             'normal_total': sum(p['count'] for u in catalog['units'] for p in u['packs']),
                             'normal_playable': sum(sum(p['count'] for p in u['packs']) for u in catalog['units'] if u['status'] != 'draft')}
    manifest['draft_sha256'] = {str(f.relative_to(out)): hashlib.sha256(f.read_bytes()).hexdigest()
                                for f in sorted((out / 'dist').rglob('*')) if f.is_file()}
    write_json(manifest_file, manifest)
    print(json.dumps(manifest['classroom'], ensure_ascii=False))


if __name__ == '__main__':
    main()
