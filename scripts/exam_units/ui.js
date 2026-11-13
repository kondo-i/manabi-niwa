// The exam syllabus references the same question IDs used by regular practice.
let examGrade = 1;
let examSubject = 'japanese';
let examSelection = new Set();
let examSearch = '';

function examButtons(grade, subject) {
    return catalog.examSections.filter(s => s.grade === grade && s.subject === subject);
}

function examPage() {
    const sections = examButtons(examGrade, examSubject);
    const visible = sections.filter(s => !examSearch || (s.chapter + ' ' + s.title).includes(examSearch));
    const grouped = Map.groupBy ? Map.groupBy(visible, s => s.chapter) : visible.reduce((groups, s) => {
        if (!groups.has(s.chapter)) groups.set(s.chapter, []);
        groups.get(s.chapter).push(s);
        return groups;
    }, new Map());
    const chosen = sections.filter(s => examSelection.has(s.id));
    return `<h1>定期テスト対策</h1>
    <p>学校のテスト範囲に合わせて、小単元を選ぼう。</p>
    <div class="exam-controls">
      <label>学年<select id="exam-grade">${catalog.grades.map(g => `<option value="${g.id}" ${g.id===examGrade?'selected':''}>${esc(g.name)}</option>`).join('')}</select></label>
      <label>教科<select id="exam-subject">${subjects.map(s => `<option value="${s.id}" ${s.id===examSubject?'selected':''}>${esc(s.name)}</option>`).join('')}</select></label>
      <form id="exam-search"><label>小単元を探す<input type="search" name="query" value="${esc(examSearch)}" placeholder="例：語彙、オーム、傾き"></label><button class="secondary">検索</button></form>
    </div>
    <div class="exam-start">
      <strong>${chosen.length}小単元を選択中</strong>
      <button class="primary" data-action="exam-start" data-size="5" ${chosen.length && chosen.length<=5?'':'disabled'}>5問練習</button>
      <button class="secondary" data-action="exam-start" data-size="20" ${chosen.length && chosen.length<=20?'':'disabled'}>20問テスト</button>
      <button class="secondary" data-action="exam-clear" ${chosen.length?'':'disabled'}>選択を解除</button>
    </div>
    ${chosen.length>20?'<p>小単元を20個以内に絞ろう。</p>':chosen.length>5?'<p>6個以上を選んだときは20問テストを使おう。</p>':''}
    ${[...grouped].map(([chapter, rows]) => `<section class="card exam-chapter">
      <h2>${esc(chapter)}</h2>
      ${rows.map(s => `<label class="exam-section"><input type="checkbox" data-exam-section="${s.id}" ${examSelection.has(s.id)?'checked':''}><span>${esc(s.title)}</span><small>${s.ids.length}問</small></label>`).join('')}
    </section>`).join('') || '<p>該当する小単元がありません。</p>'}`;
}

function examSample(sections, n, records, rng = Math.random) {
    const queues = Content.shuffled(sections,rng).map(s => ({
        section: s,
        ids: Content.shuffled(s.ids,rng).sort((a,b) =>
            Number(Boolean(records[a]?.attempts)) - Number(Boolean(records[b]?.attempts)))
    }));
    const used = new Set();
    const picked = [];
    while (picked.length < n) {
        const previous = picked.length;
        for (const queue of queues) {
            while (queue.ids.length && used.has(queue.ids[0])) queue.ids.shift();
            if (!queue.ids.length) continue;
            const id = queue.ids.shift();
            used.add(id);
            picked.push({id, section:queue.section.id});
            if (picked.length === n) break;
        }
        if (previous === picked.length) break;
    }
    return picked;
}

async function startExam(n) {
    if (busy || (state.session && !paused)) return;
    const sections = examButtons(examGrade,examSubject).filter(s=>examSelection.has(s.id));
    if (!sections.length || ![5,20].includes(n) || sections.length > n) return;
    const grade = examGrade;
    const subject = examSubject;
    const selected = examSample(sections,n,state.records);
    if (selected.length !== n) return;
    busy = true;
    render();
    try {
        const loaded = await store.byIds(selected.map(row=>row.id));
        const questions = loaded.map(q=>Generators.materialize(q));
        suspend();
        state.session = {
            id: globalThis.crypto?.randomUUID?.() ?? 'exam-' + Date.now(),
            date: day(), mode:'exam', unitId:questions[0].unitId, subject, grade,
            unitTitle:sections.length===1?sections[0].title:'定期テスト対策',
            questions, ids:questions.map(q=>q.id),
            index:0, score:0, answer:null, finished:false, recovered:[],
            orders:questions.map(q=>q.type==='choice'?Content.shuffled(q.choices.map((_,i)=>i)):[]),
            examSections: Object.fromEntries(sections.map(s=>[s.id,s.title])),
            examSequence:selected.map(row=>row.section), examResults:{}
        };
        paused = false;
        save();
    } catch (error) {
        warning = error.message;
    } finally {
        busy = false;
        render();
        window.scrollTo(0,0);
    }
}

function examResult(session) {
    if (!session.examSequence) return '';
    const entries = Object.entries(session.examResults || {});
    return `<section class="exam-results"><h3>小単元別の結果</h3>
    ${entries.map(([id,r])=>`<p>${esc(session.examSections[id])} <b>${r.correct} / ${r.total}問</b></p>`).join('')}
    <button class="secondary" data-action="exam-return">テスト範囲に戻る</button></section>`;
}

document.addEventListener('change', event => {
    const input = event.target;
    if (!['exam-grade','exam-subject'].includes(input.id) && !input.dataset.examSection) return;
    if (input.id === 'exam-grade') examGrade = Number(input.value);
    if (input.id === 'exam-subject') examSubject = input.value;
    if (input.id === 'exam-grade' || input.id === 'exam-subject') {
        examSelection.clear();
        examSearch = '';
    }
    if (input.dataset.examSection) {
        if (input.checked) examSelection.add(input.dataset.examSection);
        else examSelection.delete(input.dataset.examSection);
    }
    const focus = input.id ? '#' + input.id : `[data-exam-section="${input.dataset.examSection}"]`;
    render();
    document.querySelector(focus)?.focus({preventScroll:true});
});
document.addEventListener('submit', event => {
    if (event.target.id !== 'exam-search') return;
    event.preventDefault();
    examSearch = String(new FormData(event.target).get('query') || '').trim().slice(0,100);
    render();
    document.querySelector('#exam-search input')?.focus();
});
