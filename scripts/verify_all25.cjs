'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const [runtimeArg, previousArg, ...flags] = process.argv.slice(2);
const [runtime, previous] = [runtimeArg, previousArg].map(p => path.resolve(p));
const allowClarification = flags.includes('--allow-clarification');
let clarified = 0;
const dist = path.join(runtime, 'dist');
const read = file => fs.readFileSync(path.join(dist, file), 'utf8');
const json = file => JSON.parse(read(file));
const Content = require(path.join(dist, 'content.js'));
const Generators = require(path.join(dist, 'generators.js'));
const Routing = require(path.join(dist, 'routes.js'));
const html = fs.readFileSync(path.join(runtime, 'manabi_25.html'), 'utf8');
const embedded = JSON.parse(html.match(/const classroomAssets=([^\n]+);\n/)[1]);
const catalog = Content.validateCatalog(json('data/catalog.json'));
const prior = JSON.parse(fs.readFileSync(path.join(previous, 'dist/data/catalog.json'), 'utf8'));
const key = q => q.prompt.normalize('NFKC').replace(/\s+/g, '');
const bank = new Map();
const priorPrompts = new Set();
const addedPrompts = new Set();
const priorIds = new Set();

function verifyScoring(q) {
    const correct = q.type === 'text' ? q.answers[0] : q.answer;
    const wrong = q.type === 'choice' ? (q.answer + 1) % q.choices.length
        : q.type === 'number' ? q.answer + 10000 : '__wrong__';
    assert(Content.judge(q, correct), q.id);
    assert(!Content.judge(q, wrong), q.id);
}

function makeHarness() {
    const app = { innerHTML: '', querySelectorAll: () => [] };
    const callbacks = {};
    const location = { search: '' };
    const saved = new Map();
    const globals = {
        document: {
            addEventListener: (name, handler) => { (callbacks[name] ||= []).push(handler); },
            getElementById: id => id === 'app' ? app : {},
            querySelectorAll: () => [],
            querySelector: () => null,
        },
        window: { location, history: { pushState: (_s, _t, url) => { location.search = url; } },
                  scrollTo() {}, addEventListener() {} },
        localStorage: { getItem: k => saved.get(k), setItem: (k,v) => saved.set(k,v) },
        fetch: async file => ({ ok: true, json: async () => embedded.data[file.split('?')[0]] }),
        Content, Generators, Routing, crypto: require('node:crypto').webcrypto,
    };
    const scripts = [...read('index.html').matchAll(/<script src="([^"?]+)\?[^"]+"><\/script>/g)]
        .map(([,file]) => file);
    Object.assign(globals, globals.window);
    globals.window = globals;
    const context = vm.createContext(globals);
    for (const file of scripts) {
        if (['app.js','content.js','routes.js','generators.js'].includes(file)) continue;
        vm.runInContext(read(file), context, { filename: file });
    }
    vm.runInContext(read('app.js').replace(/^boot\(\);?\s*$/m, ''), context, { filename: 'app.js' });
    const run = code => vm.runInContext(code, context);
    const click = dataset => {
        for (const handler of callbacks.click) handler({ target: { closest: () => ({dataset}) } });
    };
    return { app, run, click };
}

async function main() {
    assert.deepEqual(embedded.data['data/catalog.json'], catalog);
    for (const u of prior.units) for (const p of u.packs) {
        const old = fs.readFileSync(path.join(previous,'dist',p.file),'utf8');
        const current = JSON.parse(read(p.file));
        const originals = JSON.parse(old);
        const comparable = current.map(q => {
            if (!allowClarification || q.id !== 'japanese-g2-auxiliary-context-balance-001:q4') return q;
            const before = originals.find(x => x.id === q.id);
            assert(before, q.id);
            assert.equal(q.prompt, '「先生が明日の予定を話される」の「れる」を、先生の動作への敬意を表す用法として読む。次のうち、同じように動作をする人への敬意を表す用法の文はどれか。');
            assert.equal(q.explanation, '設問で敬意を表すと指定した「話される」は尊敬。「校長先生が玄関に立たれる」も、校長先生の立つ動作への敬意を表す。「追いかけられる」は受け身、「思い出される」は自然に気持ちが起こる自発。');
            clarified++;
            return {...q, prompt:before.prompt, explanation:before.explanation};
        });
        assert.deepEqual(comparable, originals, p.file);
        for (const q of JSON.parse(old)) {
            priorIds.add(q.id);
            priorPrompts.add(key(q));
        }
    }
    const ready = Content.readyUnits(catalog);
    assert.equal(ready.length, catalog.units.length);
    let audio = 0;
    for (const u of ready) {
        const keys = new Set();
        for (const p of u.packs) {
            const data = json(p.file);
            assert.deepEqual(embedded.data[p.file], data);
            for (const q of Content.validatePack(data,u,p)) {
                assert(!bank.has(q.id), q.id);
                bank.set(q.id,q);
                keys.add(key(q));
                if (!priorIds.has(q.id)) {
                    assert(!priorPrompts.has(key(q)) && !addedPrompts.has(key(q)), q.id);
                    addedPrompts.add(key(q));
                }
                if (q.audio) {
                    assert(q.transcript && embedded.audio[q.audio] && fs.statSync(path.join(dist,q.audio)).size>0, q.id);
                    audio++;
                }
                if (q.figure) assert(embedded.figures[q.figure.src], q.id);
                verifyScoring(q);
                if(q.generator) verifyScoring(Generators.materialize(q,()=>0.71));
            }
        }
        assert(keys.size >= 25, u.id);
    }
    const store = Content.createStore(catalog, async p => ({ok:true,json:async()=>embedded.data[p.split('?')[0]]}));
    const context = vm.createContext({Content, document:{addEventListener(){}}});
    vm.runInContext(read('app.js').split("\n'use strict';")[0], context);
    let practiceStarts = 0;
    let examStarts = 0;
    for (const u of ready) for (const count of [5,25]) {
        const questions = await store.sample(u.id,count,()=>0.31);
        assert.equal(new Set(questions.map(q=>q.id)).size,count,u.id);
        assert(questions.every(q=>q.unitId===u.id),u.id);
        practiceStarts++;
    }
    const sections = catalog.examSections;
    assert.equal(new Set(sections.map(s=>s.id)).size,sections.length);
    for (const s of sections) {
        assert(s.ids.every(id=>bank.get(id)?.grade===s.grade && bank.get(id)?.subject===s.subject),s.id);
        assert(new Set(s.ids.map(id=>key(bank.get(id)))).size>=25,s.id);
        for (const count of [5,25]) {
            const picked = context.examSample([s],count,{},()=>0.37);
            const questions = await store.byIds(picked.map(x=>x.id));
            assert.equal(new Set(questions.map(q=>q.id)).size,count,s.id);
            examStarts++;
        }
    }
    const harness = makeHarness();
    await harness.run('boot()');
    const gradeSubject = [];
    for (const grade of catalog.grades) for (const subject of catalog.subjects) {
        harness.click({subject:subject.id});
        harness.click({grade:String(grade.id)});
        assert(!/この組み合わせの単元が見つかりません|準備中/.test(harness.app.innerHTML));
        const units = ready.filter(u=>u.grade===grade.id && u.subject===subject.id);
        assert.equal((harness.app.innerHTML.match(/data-action="practice25"/g)||[]).length,units.length);
        harness.click({action:'exam-from-units'});
        const target = sections.filter(s=>s.grade===grade.id&&s.subject===subject.id);
        assert.equal((harness.app.innerHTML.match(/data-exam-section=/g)||[]).length,target.length);
        assert(target.length>0);
        gradeSubject.push({ grade:grade.id, subject:subject.id, regular:units.length, exam:target.length });
    }
    const verifySession = count => {
        const questions = JSON.parse(harness.run('JSON.stringify(state.session.questions)'));
        assert.equal(new Set(questions.map(q=>q.id)).size,count);
        assert.equal(new Set(questions.map(key)).size,count);
    };
    let regular25 = 0, exam25 = 0;
    for (const u of ready) {
        await harness.run(`start('practice',${JSON.stringify(u.id)},25)`);
        verifySession(25);
        harness.click({action:'finish'});
        regular25++;
    }
    for (const s of sections) {
        await harness.run(`examGrade=${s.grade}; examSubject=${JSON.stringify(s.subject)};
            examSelection=new Set([${JSON.stringify(s.id)}]); startExam(25)`);
        verifySession(25);
        harness.click({action:'finish'});
        exam25++;
    }
    harness.click({subject:'science'});
    harness.click({grade:'3'});
    await harness.run("start('practice','all25-motion-data',25)");
    assert.match(harness.app.innerHTML,/1 \/ 25問/);
    for(let i=0;i<25;i++) {
        harness.run("answer(state.session.questions[state.session.index].type==='choice' ? state.session.questions[state.session.index].answer : String(state.session.questions[state.session.index].answer)); next()");
    }
    assert.equal(harness.run('state.session.score'),25);
    assert(harness.run('state.session.finished'));
    harness.click({action:'finish'});
    harness.click({subject:'science'});
    harness.click({grade:'3'});
    harness.click({action:'exam-from-units'});
    await harness.run("examSelection = new Set(['all25-forces','all25-motion-data','all25-power']); startExam(25)");
    assert.match(harness.app.innerHTML,/1 \/ 25問/);
    for(let i=0;i<25;i++) {
        harness.run("answer(state.session.questions[state.session.index].type==='choice' ? state.session.questions[state.session.index].answer : String(state.session.questions[state.session.index].answer)); next()");
    }
    assert.equal(harness.run('state.session.score'),25);
    assert.match(harness.app.innerHTML,/小単元別の結果/);
    assert.deepEqual(JSON.parse(harness.run('JSON.stringify(Object.values(state.session.examResults).map(x=>x.total).sort())')),[8,8,9]);
    harness.click({action:'exam-return'});
    assert.match(harness.app.innerHTML,/3小単元を選択中/);

    const publicationRuns = [];
    for (const [uid, grade, subject, companion] of [
        ['repair-science-g3-buoyancy', 3, 'science', 'all25-forces'],
        ['repair-math-g2-boxplots', 2, 'math', 'exam-section-051'],
    ]) {
        if (!ready.some(u => u.id === uid)) continue;
        harness.click({action:'finish'});
        await harness.run(`start('practice',${JSON.stringify(uid)},25)`);
        verifySession(25);
        for (let i=0; i<25; i++) harness.run("answer(state.session.questions[state.session.index].type==='choice' ? state.session.questions[state.session.index].answer : String(state.session.questions[state.session.index].answer)); next()");
        assert.equal(harness.run('state.session.score'),25);
        assert(harness.run('state.session.finished'));
        harness.click({action:'finish'});
        await harness.run(`examGrade=${grade}; examSubject=${JSON.stringify(subject)}; examSelection=new Set(${JSON.stringify([uid,companion])}); startExam(25)`);
        verifySession(25);
        for (let i=0; i<25; i++) harness.run("answer(state.session.questions[state.session.index].type==='choice' ? state.session.questions[state.session.index].answer : String(state.session.questions[state.session.index].answer)); next()");
        assert.equal(harness.run('state.session.score'),25);
        assert.match(harness.app.innerHTML,/小単元別の結果/);
        assert.deepEqual(JSON.parse(harness.run('JSON.stringify(Object.values(state.session.examResults).map(x=>x.total).sort((a,b)=>a-b))')),[12,13]);
        publicationRuns.push({unit:uid, practiceScore:25, mixedExamScore:25, distribution:[12,13]});
    }

    if (allowClarification) assert.equal(clarified, 1);
    const report = { uniqueQuestions:bank.size, priorQuestionsPreserved:priorIds.size - clarified,
        questionsClarified:clarified,
        newUniquePromptQuestions:addedPrompts.size, audioFiles:audio, practiceStarts, examStarts, regular25, exam25,
        gradeSubject, completedG3ScienceRuns:[{mode:'practice',score:25},{mode:'exam',score:25,distribution:[8,8,9]}],
        completedPublicationRuns:publicationRuns };
    fs.writeFileSync(path.join(runtime,'verification.json'), JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report));
}
main().catch(err=>{console.error(err);process.exitCode=1});
