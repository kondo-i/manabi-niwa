"""Build the selectable exam syllabus and single-file student edition."""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_release_runtime_v2 import offline_html, write_json, SUBJECTS
from exam_units.new_items import english_items, math_items, science_items
from unit20.common import choice, word

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/exam_units'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f'Unexpected base UI: {before}')
    return text.replace(before, after, 1)


def fact_bank():
    groups = defaultdict(list)
    for line in (DATA / 'facts.txt').read_text(encoding='utf-8').splitlines():
        if line.startswith('@'):
            key = line[1:]
        elif line.strip():
            groups[key].append(line.split('|'))
    return groups


def fact_items(key, facts):
    rows = facts[key]
    result = []
    assert len(rows) == 10, key
    for i, (cue, answer, explanation) in enumerate(rows):
        other = list(dict.fromkeys(row[1] for row in rows[i+1:] + rows[:i] if row[1] != answer))
        if key in ('historical-kana','old-words'):
            prompt = f'「{cue}」の{"現代仮名遣い" if key=="historical-kana" else "古文での意味"}として適切なのは？'
            recall = (f'「{cue}」を現代仮名遣いに直し、ひらがなで書こう。' if key=='historical-kana'
                      else f'古語の「{cue}」の意味を確かめよう。')
        else:
            prompt = f'次に当てはまるものを選ぼう。\n{cue}'
            recall = f'次に当てはまる答えを書こう。\n{cue}'
        result.append(choice(prompt, answer, other[0], other[1], explanation))
        if key in ('old-words','kanbun','construction','congruence','refraction-lens','chemical-formulas',
                   'meters','magnetism','fronts','neutralization','battery','cell-division','moon','seasons','ecosystem',
                   'world-war-two','government','rights'):
            result.append(choice(f'「{answer}」について、次のうちこの組み合わせに合う説明は？\n{cue}',
                                 explanation, rows[(i+1)%10][2], rows[(i+2)%10][2], explanation))
        else:
            result.append(word(recall, answer, explanation))
    return result


def add_unit(dist, catalog, bank, unit_id, grade, subject, title, questions, description):
    assert questions
    added_ids = []
    packs = []
    for start in range(0, len(questions), 100):
        pack = f'{unit_id}-p{start//100+1}'
        items = []
        for i, q in enumerate(questions[start:start+100], 1):
            item = dict(q, id=q.get('id', f'{pack}:q{i:02}'), unitId=unit_id,
                        grade=grade, subject=subject, status='prototype')
            assert item['id'] not in bank, item['id']
            bank[item['id']] = item
            added_ids.append(item['id'])
            items.append(item)
        file = f'data/packs/{pack}.json'
        write_json(dist / file, items)
        packs.append(dict(id=pack,file=file,revision=digest((dist/file).read_bytes())[:12],
                          count=len(items),randomized=False,
                          legacyIds=[q['id'] for q in items if not q['id'].startswith(pack+':')]))
    catalog['units'].append(dict(id=unit_id, grade=grade, subject=subject, title=title,
                                 status='prototype',description=description,packs=packs))
    return added_ids


def section(id, grade, subject, chapter, title, ids, sources, kind):
    return dict(id=id, grade=grade, subject=subject, chapter=chapter, title=title,
                ids=list(dict.fromkeys(ids)), sourceUnits=sources, kind=kind)


def vocabulary_sections(dist, catalog, bank, vocabulary):
    source = read_json(vocabulary)
    assert len(source) == 1040
    groups = defaultdict(dict)
    reading = defaultdict(list)
    for q in source:
        assert q['choices'][q['correct_index']]==q['correct_answer'], q['id']
        item = dict(id=q['id'],type='choice',prompt=q['prompt'],choices=q['choices'],
                    answer=q['correct_index'],explanation=q['explanation'])
        if q['question_type']=='logical_reading':
            reading[q['grade']].append(item)
            continue
        assert q['question_type'] in {'meaning','context'}
        assert q['grade'] in (1,2,3)
        category = '抽象語とことばの使い分け' if q['grade']==3 else q['category']
        groups[q['grade'],category].setdefault(q['lexeme_id'],[]).append((q['topic'],item))
    sections=[]
    for (grade, category), words in groups.items():
        rows=list(words.values())
        assert all(len(row)==2 for row in rows)
        while rows:
            size=10 if len(rows)>=20 else len(rows)
            batch,rows=rows[:size],rows[size:]
            topics=list(dict.fromkeys(topic for pair in batch for topic,_ in pair))
            title=category+'｜'+'・'.join(topics)
            uid=f'exam-vocab-g{grade}-{len(sections)+1:02}'
            ids=add_unit(dist,catalog,bank,uid,grade,'japanese',title,
                         [q for pair in batch for _,q in pair],'語の意味と文脈での使い分け')
            sections.append(section(uid,grade,'japanese','語彙力',title,ids,[uid],'vocabulary'))
    for line in (DATA / 'reading.txt').read_text(encoding='utf-8').splitlines():
        grade, prompt, answer, wrong_a, wrong_b, explanation = line.split('|')
        reading[int(grade)].append(choice(prompt.replace(r'\n', '\n'), answer, wrong_a, wrong_b, explanation))
    for grade, items in sorted(reading.items()):
        uid=f'exam-logic-g{grade}'
        ids=add_unit(dist,catalog,bank,uid,grade,'japanese','論理的読解の短文演習',items,'短い文章の対比・因果・要旨')
        sections.append(section(uid,grade,'japanese','読解','論理的読解の短文演習',ids,[uid],'reading'))
    return sections


def update_app(dist, section_count, question_count):
    app=dist/'app.js'
    js=app.read_text(encoding='utf-8')
    js=replace_once(js,'({home,subjects:units,review','({home,exam:examPage,subjects:units,review')
    js=replace_once(js,'${growthResult(s)}${campResult(s)}','${examResult(s)}${growthResult(s)}${campResult(s)}')
    js=replace_once(js,'s.score+=Number(ok);','''s.score+=Number(ok);
 if(s.examSequence){const key=s.examSequence[s.index];const entry=s.examResults[key]||{total:0,correct:0};entry.total++;entry.correct+=Number(ok);s.examResults[key]=entry;}
 ''')
    js=replace_once(js,"if(a==='clear-filter')",'''if(a==='exam-start'){startExam(Number(b.dataset.size));return}
 if(a==='exam-clear'){examSelection.clear();render();return}
 if(a==='exam-return'){examGrade=state.session.grade;examSubject=state.session.subject;examSelection=new Set(Object.keys(state.session.examSections));examSearch='';state.session=null;paused=false;page='exam';save();syncRoute();render();window.scrollTo(0,0);return}
 if(a==='clear-filter')''')
    ui=(ROOT/'scripts/exam_units/ui.js').read_text(encoding='utf-8')
    # Register the syllabus UI before the app's asynchronous initialization.
    js=ui+'\n'+js
    app.write_text(js,encoding='utf-8')
    routes=dist/'routes.js'
    routes.write_text(replace_once(routes.read_text(), "pages=['home','subjects'", "pages=['home','exam','subjects'"))
    index=dist/'index.html'
    html=index.read_text(encoding='utf-8')
    html=replace_once(html,'<button data-page="subjects">', '<button data-page="exam">定期テスト対策</button><button data-page="subjects">')
    html=replace_once(html,'<nav class="classroom-nav" aria-label="学年と教科を選ぶ">',
                      '<nav class="classroom-nav" aria-label="学年と教科を選ぶ"><button class="primary" data-page="exam">定期テスト対策</button>')
    html=replace_once(html,'<body>', '<style>'+(ROOT/'scripts/exam_units/ui.css').read_text()+'</style><body>')
    html=replace_once(html, '授業練習版。201単元、通常問題4,323問。',
                      f'定期テスト対策 {section_count}小単元・学習問題 全{question_count:,}問。')
    index.write_text(html,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--base',type=Path,help='Already generated unit20 runtime')
    parser.add_argument('--vocabulary',type=Path,required=True,help='Japanese v10 questions.json')
    args=parser.parse_args()
    out=args.output.resolve()
    if args.base:
        out.mkdir(parents=True,exist_ok=False)
        shutil.copytree(args.base/'dist',out/'dist',ignore=shutil.ignore_patterns('practice.html'))
    else:
        subprocess.run([sys.executable,str(ROOT/'scripts/build_unit20.py'),str(out)],check=True)
    dist=out/'dist'
    catalog_file=dist/'data/catalog.json'
    catalog=read_json(catalog_file)
    original_units=list(catalog['units'])
    bank={q['id']:q for u in original_units for p in u['packs'] for q in read_json(dist/p['file'])}
    original_count=len(bank)
    by_unit=defaultdict(list)
    for q in bank.values():
        by_unit[q['unitId']].append(q)
    facts=fact_bank()
    sections=[]
    for i,line in enumerate((DATA/'sections.tsv').read_text(encoding='utf-8').splitlines(),1):
        grade,subject,chapter,title,source=line.split('\t')
        grade=int(grade)
        uid=f'exam-section-{i:03}'
        if source.startswith('+'):
            key=source[1:]
            factory={'math':math_items,'science':science_items,'english':english_items}.get(subject)
            questions=factory(key) if factory else []
            if not questions:
                questions=fact_items(key,facts)
            ids=add_unit(dist,catalog,bank,uid,grade,subject,title,questions,chapter)
            sources=[uid]
            kind='new'
        else:
            sources=source.split()
            ids=[q['id'] for u in sources for q in by_unit[u]]
            kind='existing'
        sections.append(section(uid,grade,subject,chapter,title,ids,sources,kind))
    sections+=vocabulary_sections(dist,catalog,bank,args.vocabulary)
    for s in sections:
        assert len(s['ids'])>=20, s['title']
        assert all((bank[id]['grade'],bank[id]['subject'])==(s['grade'],s['subject']) for id in s['ids']),s['title']
    catalog['examSections']=sections
    write_json(catalog_file,catalog)
    update_app(dist,len(sections),len(bank))
    html=offline_html(dist)
    # The study menu uses the same hash routing as the standalone app.
    (out/'manabi_exam.html').write_text(html,encoding='utf-8')
    columns=['grade','subject','chapter','title','count','kind','source_units']
    with (out/'exam_sections.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(columns)
        for s in sorted(sections,key=lambda s:(s['grade'],s['subject'],s['chapter'],s['title'])):
            writer.writerow([s['grade'],SUBJECTS[s['subject']],s['chapter'],s['title'],len(s['ids']),s['kind'],' '.join(s['sourceUnits'])])
    tested_ids={id for s in sections for id in s['ids']}
    with (out/'teacher_exam_answers.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['ID','学年','教科','問題','正答','解説','音声原稿'])
        for id in sorted(tested_ids):
            q=bank[id]
            answer=q['choices'][q['answer']] if q['type']=='choice' else ' / '.join(q['answers']) if q['type']=='text' else q['answer']
            writer.writerow([id,q['grade'],SUBJECTS[q['subject']],q['prompt'],answer,q['explanation'],q.get('transcript','')])
    summary=dict(previous_units=len(original_units),previous_questions=original_count,
                 exam_sections=len(sections),exam_question_ids=len(tested_ids),total_questions=len(bank),
                 section_min=min(len(s['ids']) for s in sections),
                 by_cell=dict(sorted(Counter(f"{s['subject']}_g{s['grade']}" for s in sections).items())),
                 by_kind=Counter(s['kind'] for s in sections),vocabulary_sha256=digest(args.vocabulary.read_bytes()))
    write_json(out/'exam_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    main()
