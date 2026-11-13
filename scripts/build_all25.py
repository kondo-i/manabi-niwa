"""Build the all-grades classroom edition from the exam draft and vocabulary source."""
import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from all25.items import paired_items, skills, unreal_items
from build_exam_units import add_unit, digest, fact_bank, read_json, replace_once, section
from build_release_runtime_v2 import SUBJECTS, add_audio, offline_html, write_json
from build_unit20 import GENERATORS, prompt_key
from unit20.common import cards, choice

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/all25'
MINIMUM = 25


def add_reviewed_material(dist, catalog, bank, existing, sections):
    """Add bounded, source-reviewed supplements; keep original item IDs intact."""
    materials = [
        ('math_primes.json', 'repair-math-g1-primes', 1, 'math',
         '数と式', '素数と素因数分解'),
        ('english_obligation.json', 'repair-english-g2-obligation', 2, 'english',
         '助動詞', '義務・禁止・不必要の使い分け'),
        ('science_material.json', 'repair-science-g3-data', 3, 'science',
         '実験・資料読解', '中3理科の実験・資料読解'),
    ]
    descriptions = {
        'repair-math-g1-primes': '素数の意味、素因数分解の手順、誤りの直し方と活用を練習する25問。',
        'repair-english-g2-obligation': 'must・have toの義務と、禁止・不必要を場面や案内から読み分ける25問。',
        'repair-science-g3-data': '学習用に作成した記録表・グラフ・模型から、条件と理由を考える25問。',
    }
    for filename, uid, grade, subject, chapter, title in materials:
        questions = read_json(ROOT / 'data/coverage_repair' / filename)
        assert len(questions) >= MINIMUM, filename
        assert all(q['unitId'] == uid and q['grade'] == grade and
                   q['subject'] == subject for q in questions), filename
        assert len({prompt_key(q['prompt']) for q in questions}) == len(questions), filename
        ids = add_unit(dist, catalog, bank, uid, grade, subject, title, questions, descriptions[uid])
        existing[uid] = [bank[qid] for qid in ids]
        sections.append(section(uid, grade, subject, chapter, title, ids, [uid], 'reviewed-supplement'))
    for source in (ROOT / 'data/coverage_repair').glob('*.svg'):
        target = dist / 'data/figures' / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def groups(file):
    result = defaultdict(list)
    for line in (DATA / file).read_text(encoding='utf-8').splitlines():
        if line.startswith('@'):
            key = line[1:]
        elif line.strip():
            result[key].append(line.replace(r'\n', '\n'))
    return result


def make_supplement(unit, existing, previous_sections, vocabulary, legacy, reading, facts, used):
    uid, subject = unit['id'], unit['subject']
    needed = MINIMUM - len({prompt_key(q['prompt']) for q in existing})
    if needed <= 0:
        return []
    if uid.startswith('exam-vocab-'):
        pairs = []
        for q in existing:
            source = vocabulary[q['id']]
            if source['question_type'] == 'meaning':
                scene = vocabulary[q['id'].removesuffix('-M') + '-C']
                a, b = (word for word in scene['choices'] if word != source['target_word'])
                pairs.append(choice(
                    f'【語彙の逆引き】\n「{source["correct_answer"]}」に最も近い言葉は？',
                    source['target_word'], a, b,
                    f'正答は「{source["target_word"]}」。{source["explanation"]}'))
        candidates = pairs
    elif uid.startswith('exam-logic-'):
        candidates = [choice(*line.split('|')) for line in reading[uid]]
    elif uid in previous_sections:
        key = previous_sections[uid]
        if key in facts:
            rows = facts[key]
            candidates = []
            for i, (cue, answer, explanation) in enumerate(rows):
                wrong = list(dict.fromkeys(row[1] for row in rows[i+1:]+rows[:i] if row[1] != answer))
                if key in ('historical-kana','old-words'):
                    question = f'「{cue}」の{"現代仮名遣い" if key=="historical-kana" else "古文での意味"}'
                else:
                    question = cue
                candidates.append(choice(
                    f'【答えと理由】\n{question}に合う答えと説明の組は？',
                    f'{answer} ― {explanation}',
                    f'{wrong[0]} ― {rows[(i+1)%len(rows)][2]}',
                    f'{wrong[1]} ― {rows[(i+2)%len(rows)][2]}',
                    explanation))
        else:
            from exam_units.new_items import english_items, math_items, science_items
            factory = {'english': english_items, 'math': math_items, 'science': science_items}[subject]
            candidates = factory(key, count=36)[20:]
    else:
        candidates = cards('\n'.join(legacy[uid])) if legacy[uid] else []
        if uid in ('exp-math-g3-factorization','exp-math-g3-quadratic-function'):
            candidates += skills(uid.removeprefix('exp-math-g3-'), 15, 20)
        if len(candidates) < needed:
            candidates += [GENERATORS[subject].generate(uid, i) for i in range(80)]
    result = []
    for q in candidates:
        normalized = prompt_key(q['prompt'])
        if normalized in used:
            continue
        used.add(normalized)
        result.append(q)
        if len(result) == needed:
            break
    if len(result) != needed:
        raise ValueError(f'{uid} needs {needed} more questions but only {len(result)} were available')
    return result


def add_pack(dist, unit, additions):
    uid = unit['id']
    pid = f'{uid}-all25'
    for i, q in enumerate(additions, 1):
        q.update(id=f'{pid}:q{i:02}', unitId=uid, grade=unit['grade'], subject=unit['subject'], status='prototype')
        if q.get('transcript'):
            q['audio'] = f'data/audio/{pid}-q{i:02}.mp3'
            add_audio(dist/q['audio'], q['transcript'])
    file = f'data/packs/{pid}.json'
    write_json(dist/file, additions)
    unit['packs'].append(dict(id=pid, file=file, revision=digest((dist/file).read_bytes())[:12],
                              count=len(additions), randomized=False))
    unit['status'] = 'prototype'


def update_interface(dist, sections, total, prompt_aliases, practice_ids):
    app = dist/'app.js'
    js = app.read_text()
    replacements = [
        ('[5,20].includes(n)', '[5,25].includes(n)'),
        ('data-size="20"', 'data-size="25"'),
        ('>20問テスト', '>25問テスト'),
        ('ときは20問テスト', 'ときは25問テスト'),
        ('<=20', '<=25'),
        ('>20?', '>25?'),
        ('20個以内', '25個以内'),
    ]
    original = (ROOT/'scripts/exam_units/ui.js').read_text()
    assert js.startswith(original)
    updated = original
    for before, after in replacements:
        updated = replace_once(updated, before, after)
    js = 'const practiceUnitIds=' + json.dumps(practice_ids) + ';\nconst examPromptKeys=' + json.dumps(prompt_aliases) + ';\n' + updated + (ROOT/'scripts/all25/distinct.js').read_text() + js[len(original):]
    js = replace_once(js, 'while (queue.ids.length && used.has(queue.ids[0])) queue.ids.shift();',
        'while (queue.ids.length && used.has(examPromptKeys[queue.ids[0]] || queue.ids[0])) queue.ids.shift();')
    js = replace_once(js, 'used.add(id);', 'used.add(examPromptKeys[id] || id);')
    js = replace_once(js, 'const questions = loaded.map(q=>Generators.materialize(q));',
        'const questions = distinctQuizQuestions(loaded);')
    js = replace_once(js,"if(a==='practice20'){start('practice',b.dataset.unit,20);return}",
        "if(a==='practice25'){start('practice',b.dataset.unit,25);return}")
    js = replace_once(js, "if(mode==='warmup')questions=", """if(mode==='practice' && n===25){
        const allIds = practiceUnitIds[unitId];
        const recent = id => state.records[id]?.attempts || 0;
        const ids = Content.shuffled(allIds).sort((a,b) => recent(a)-recent(b));
        const seen = new Set();
        const distinct = ids.filter(id => {
            const key = examPromptKeys[id] || id;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        }).slice(0,n);
        questions = distinctQuizQuestions(await store.byIds(distinct));
    }
    if(mode==='warmup')questions=""")
    js = replace_once(js, 'else questions=await store.sample', "else if(mode!=='practice'||n!==25)questions=await store.sample")
    js = replace_once(js, 'data-action="practice20" data-unit="${u.id}">20問に挑戦',
        'data-action="practice25" data-unit="${u.id}">25問に挑戦')
    js = replace_once(js, "selectedGrade=Number(b.dataset.grade);selectedTopic='';selectedUnit='';",
        "selectedGrade=Number(b.dataset.grade);selectedTopic='';selectedUnit='';query='';")
    js = replace_once(js, "${selectedSubject==='science'?\x60<div class=\"topic-filters\"",
        "${selectedSubject==='science'&&selectedGrade<=1?\x60<div class=\"topic-filters\"")
    start, end = js.index('function units()'), js.index('function review()')
    unit_screen = replace_once(js[start:end], '${list.length?`<div class="grid">', '${selectedGrade?`<button class="primary" data-action="exam-from-units">この学年・教科の小単元を選ぶ →</button>`:\'\'}${list.length?`<div class="grid">')
    js = js[:start] + unit_screen + js[end:]
    js = replace_once(js, "if(a==='exam-start')",
        "if(a==='exam-from-units'){examGrade=selectedGrade;examSubject=selectedSubject;examSelection.clear();examSearch='';page='exam';syncRoute();render();window.scrollTo(0,0);return}\n if(a==='exam-start')")
    js = replace_once(js, "query?'一致する単元がありません':'この学年の教材は準備中です'",
                      "(query||selectedTopic||selectedUnit)?'条件に合う単元がありません':'この組み合わせの単元が見つかりません'")
    js = js.replace('href="?unit=', 'href="?page=subjects&unit=')
    js = js.replace('href="?topic=', 'href="?page=subjects&topic=')
    js = replace_once(js, '<button class="primary" data-action="finish">ホームに戻る →</button></section>',
        '${s.score<s.ids.length?\'<p>間違えた問題は「もう一度」に保存されます。解説を読んで、明日また練習しよう。</p><button class="secondary" data-page="review">間違えた問題を復習する →</button>\':\'\'}'
        '<button class="primary" data-action="finish">ホームに戻る →</button></section>')
    js += '\n' + (ROOT / 'scripts/coverage_repair/figure_zoom.js').read_text(encoding='utf-8')
    app.write_text(js, encoding='utf-8')
    index = dist/'index.html'
    html = index.read_text()
    html = replace_once(html, 'おためし版', '全単元25問以上')
    html = replace_once(html, '定期テスト対策 236小単元・学習問題 全6,463問。',f'定期テスト対策 {sections}小単元・学習問題 全{total:,}問。')
    index.write_text(html, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--vocabulary', type=Path, required=True)
    parser.add_argument('--exam-base', type=Path, help='Previously built exam runtime at the pinned revision')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir()
    if args.exam_base:
        shutil.copytree(args.exam_base/'dist', out/'dist', ignore=shutil.ignore_patterns('practice.html', 'exam.html'))
    else:
        subprocess.run([sys.executable, str(ROOT/'scripts/build_exam_units.py'), str(out/'exam-base'),
                        '--vocabulary', str(args.vocabulary.resolve())], check=True)
        shutil.move(out/'exam-base/dist', out/'dist')
        shutil.rmtree(out/'exam-base')
    dist = out/'dist'
    path = dist/'data/catalog.json'
    catalog = read_json(path)
    existing = {u['id']: [q for p in u['packs'] for q in read_json(dist/p['file'])] for u in catalog['units']}
    used = {prompt_key(q['prompt']) for questions in existing.values() for q in questions}
    vocab = {q['id']:q for q in read_json(args.vocabulary)}
    prior_sections = {}
    for i, line in enumerate((ROOT/'data/exam_units/sections.tsv').read_text().splitlines(), 1):
        key = line.split('\t')[-1]
        if key.startswith('+'):
            prior_sections[f'exam-section-{i:03}'] = key[1:]
    legacy, reading, facts = groups('legacy.txt'), groups('reading.txt'), fact_bank()
    bank = {q['id']:q for qs in existing.values() for q in qs}
    errors = []
    for u in catalog['units']:
        uid = u['id']
        try:
            items = make_supplement(u, existing[uid], prior_sections, vocab, legacy, reading, facts, used)
        except (ValueError, AssertionError, KeyError, IndexError) as error:
            errors.append((uid,str(error)))
            continue
        if items:
            add_pack(dist, u, items)
            existing[uid].extend(items)
            bank.update((q['id'], q) for q in items)
    if errors:
        raise ValueError('Supplement failures:\n'+'\n'.join(f'{uid}: {error}' for uid,error in errors))
    sections = catalog['examSections']
    for s in sections:
        s['ids'] = list(dict.fromkeys(q['id'] for uid in s['sourceUnits'] for q in existing[uid]))

    concept_rows = groups('regions.txt')
    application = groups('applications.txt')
    for line in (DATA/'sections.tsv').read_text().splitlines():
        grade, subject, chapter, title, key = line.split('\t')
        uid = f'all25-{key}'
        authored = [choice(*row.split('|')) for row in application[key]]
        if key in concept_rows:
            candidates = paired_items([tuple(row.split('|')) for row in concept_rows[key]])
        elif key == 'unreal':
            candidates = unreal_items()
        else:
            candidates = skills(key, 45)
        items = []
        for q in authored+candidates:
            normalized = prompt_key(q['prompt'])
            if normalized not in used:
                items.append(q)
                used.add(normalized)
            if len(items)==MINIMUM:
                break
        if len(items) < MINIMUM:
            raise ValueError(f'{key}: only {len(items)} distinct questions')
        ids = add_unit(dist, catalog, bank, uid, int(grade), subject, title, items, chapter)
        sections.append(section(uid, int(grade), subject, chapter, title, ids, [uid], 'new'))
        existing[uid] = [bank[qid] for qid in ids]
    add_reviewed_material(dist, catalog, bank, existing, sections)
    unit_counts = {u['id']:len(existing[u['id']]) for u in catalog['units']}
    assert min(len({prompt_key(q['prompt']) for q in existing[u['id']]}) for u in catalog['units']) >= MINIMUM
    assert all(len({prompt_key(bank[qid]['prompt']) for qid in s['ids']}) >= MINIMUM for s in sections)
    write_json(path, catalog)
    repeated = defaultdict(list)
    for qid,q in bank.items():
        repeated[prompt_key(q['prompt'])].append(qid)
    aliases = {qid: ids[0] for ids in repeated.values() if len(ids)>1 for qid in ids}
    update_interface(dist, len(sections), len(bank), aliases,
                     {uid:[q['id'] for q in qs] for uid,qs in existing.items()})
    (out/'manabi_25.html').write_text(offline_html(dist), encoding='utf-8')
    tested = {qid for s in sections for qid in s['ids']}
    summary = dict(regular_units=len(unit_counts), exam_sections=len(sections),
                   unique_questions=len(bank), new_questions=len(bank)-6463, exam_questions=len(tested),
                   min_regular=min(unit_counts.values()), min_exam=min(len(s['ids']) for s in sections),
                   by_exam_grade_subject=dict(sorted(Counter(f"{s['subject']}_g{s['grade']}" for s in sections).items())),
                   by_regular_grade_subject=dict(sorted(Counter(f"{s['subject']}_g{s['grade']}" for s in catalog['units']).items())))
    write_json(out/'summary.json', summary)
    with (out/'unit_counts.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(['画面','学年','教科','章','単元','ID','問題数'])
        for u in catalog['units']:
            writer.writerow(['通常',u['grade'],SUBJECTS[u['subject']],'',u['title'],u['id'],unit_counts[u['id']]])
        for s in sections:
            writer.writerow(['定期テスト対策',s['grade'],SUBJECTS[s['subject']],s['chapter'],s['title'],s['id'],len(s['ids'])])
    with (out/'teacher_answers.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(['ID','学年','教科','単元','問題','選択肢','正答','解説','音声原稿'])
        title = {u['id']:u['title'] for u in catalog['units']}
        for qid,q in sorted(bank.items()):
            answer = q['choices'][q['answer']] if q['type']=='choice' else ' / '.join(q['answers']) if q['type']=='text' else q['answer']
            writer.writerow([qid,q['grade'],SUBJECTS[q['subject']],title[q['unitId']],q['prompt'],
                             ' / '.join(q.get('choices',[])),answer,q['explanation'],q.get('transcript','')])
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
