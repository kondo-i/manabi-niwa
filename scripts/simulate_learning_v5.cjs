'use strict';
// Exercise actual runtime handlers with a simulated DOM and browser storage.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const runtimeRoot = path.resolve(process.argv[2] || '.');
const dist = path.join(runtimeRoot, 'dist');
const fixtures = path.join(__dirname, '../reports/app_review/v3');
const output = path.resolve(process.argv[3] || fs.mkdtempSync(require('node:os').tmpdir()+'/manabi-app-v4-'));
fs.mkdirSync(output,{recursive:true});
const readJson = filename => JSON.parse(fs.readFileSync(filename, 'utf8'));
const manifest = readJson(path.join(runtimeRoot, 'source-manifest.json'));
const questions = readJson(path.join(fixtures, 'questions.json'));
const oldQuestions = readJson(path.join(__dirname, '../reports/app_review/added_185_questions.json')).map(item => item.question);
const challengeBank = readJson(path.join(dist, 'data/stretch-bank.json'));
const Content = require(path.join(dist, 'content.js'));
const Strengths = require(path.join(dist, 'strengths.js'));
const seedValue = 20261105;
let randomState = seedValue;
Math.random = () => {
    randomState = (Math.imul(randomState, 1664525) + 1013904223) >>> 0;
    return randomState / 2 ** 32;
};

async function flush() {
    for (let index = 0; index < 18; index++) {
        await new Promise(resolve => setImmediate(resolve));
    }
}

function emptyState() {
    return { records: {}, days: [], completed: [], xp: 0, session: null };
}

function decodeEntities(text) {
    const entities = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'" };
    return text.replace(/&amp;|&lt;|&gt;|&quot;|&#39;/g, value => entities[value]);
}

async function browser(saved = emptyState()) {
    let html = '';
    let stored = JSON.stringify(saved);
    const listeners = {};
    const app = {
        set innerHTML(value) { html = value; },
        get innerHTML() { return html; },
        querySelectorAll() { return []; },
    };
    const environment = {
        console, Math, crypto: crypto.webcrypto,
        FormData: class {
            constructor(form) { this.form = form; }
            get(key) { return this.form[key]; }
        },
        window: { scrollTo() {} },
        document: {
            getElementById: id => id === 'app' ? app : {},
            querySelectorAll: () => [],
            addEventListener: (type, callback) => { listeners[type] = callback; },
        },
        localStorage: {
            getItem: () => stored,
            setItem: (key, value) => { stored = value; },
        },
        fetch: async filename => ({
            ok: true,
            json: async () => readJson(path.join(dist, filename.split('?')[0])),
        }),
    };
    const modules = {
        Content: 'content', Strengths: 'strengths', Growth: 'progress', GardenCamp: 'garden-camp',
        RPG: 'rpg', RepairScene: 'repair-scene', Adventure: 'adventure-routes',
        DensityLab: 'density-lab', LightLab: 'light-lab', SpringLab: 'spring-lab',
        Journey: 'journey', Routing: 'routes',
    };
    for (const [symbol, file] of Object.entries(modules)) {
        environment[symbol] = require(path.join(dist, file + '.js'));
    }
    const context = vm.createContext(environment);
    for (const filename of ['strength-ui.js', 'app.js']) {
        vm.runInContext(fs.readFileSync(path.join(dist, filename), 'utf8'), context);
    }
    await flush();
    const navigation = fs.readFileSync(path.join(dist, 'index.html'), 'utf8').match(/<nav>[\s\S]*?<\/nav>/)?.[0] || '';
    function buttons() {
        return [...(navigation + html).matchAll(/<button\b([^>]*)>(.*?)<\/button>/gs)].map(match => ({
            dataset: Object.fromEntries([...match[1].matchAll(/data-([\w-]+)="([^"]*)"/g)]
                .map(attribute => [attribute[1], attribute[2]])),
            disabled: /\bdisabled\b/.test(match[1]),
            label: decodeEntities(match[2].replace(/<[^>]*>/g, '')).trim(),
        }));
    }
    const api = {
        get html() { return decodeEntities(html); },
        get state() { return JSON.parse(stored); },
        buttons,
        async click(attributes) {
            const button = buttons().find(candidate => !candidate.disabled
                && Object.entries(attributes).every(([key, value]) => candidate.dataset[key] === String(value)));
            assert(button, 'Missing enabled button ' + JSON.stringify(attributes));
            listeners.click({ target: { closest: () => button } });
            await flush();
        },
        async answer(question, correct) {
            if (question.type === 'choice') {
                await api.click({ answer: correct ? question.answer : (question.answer + 1) % question.choices.length });
            } else {
                assert(html.includes('id="typed-answer"'));
                const answer = correct ? String(question.answers?.[0] ?? question.answer) : '999999';
                listeners.submit({ target: { id: 'typed-answer', answer }, preventDefault() {} });
                await flush();
            }
        },
    };
    return api;
}

async function main() {
    let checkedFiles = 0;
    for (const [filename, expected] of Object.entries(manifest.draft_sha256)) {
        const actual = crypto.createHash('sha256').update(fs.readFileSync(path.join(runtimeRoot, filename))).digest('hex');
        assert.equal(actual, expected, filename);
        checkedFiles++;
    }
    Strengths.validateBank(challengeBank);
    const originalById = new Map(oldQuestions.map(question => [question.id, question]));
    const revisedNormal = questions.filter(question => !question.id.startsWith('stretch-')
        && JSON.stringify(question) !== JSON.stringify(originalById.get(question.id)));
    const results = [];
    for (const target of revisedNormal) {
        const saved = emptyState();
        saved.focusSubject = target.subject;
        saved.records[target.id] = { attempts: 1, correct: 0, lastCorrect: false, lastDate: '2026-11-04' };
        const page = await browser(saved);
        await page.click({ page: 'review' });
        await page.click({ action: 'review', unit: target.unitId });
        const actual = page.state.session.questions[0];
        assert.equal(actual.id, target.id);
        assert.deepEqual(actual.choices, target.choices);
        assert.equal(actual.prompt, target.prompt);
        assert(page.html.includes(target.prompt));
        await page.answer(actual, true);
        assert(page.html.includes(target.explanation));
        await page.click({ action: 'next' });
        assert.equal(page.state.records[target.id].lastCorrect, true);
        results.push({ id: target.id, entry: 'review_button', prompt_and_choices: 'PASS', saved_correctness: 'PASS' });
    }
    for (const target of challengeBank) {
        const saved = emptyState();
        saved.focusSubject = target.subject;
        for (const question of challengeBank.filter(question => question.subject === target.subject && question.id !== target.id)) {
            saved.records[question.id] = { attempts: 1, correct: 0, lastDate: '2026-11-04', isStretch: true };
        }
        const page = await browser(saved);
        await page.click({ action: 'stretch-start', item: target.subject });
        assert.equal(page.state.session.questions[0].id, target.id);
        assert(page.html.includes(target.prompt));
        await page.click({ action: 'stretch-hint' });
        await page.click({ action: 'stretch-hint' });
        assert(page.html.includes(target.hints[0]) && page.html.includes(target.hints[1]));
        await page.answer(target, true);
        assert(page.html.includes(target.explanation));
        await page.click({ action: 'next' });
        assert(Number.isFinite(page.state.records[target.id].lastAt));
        assert.equal(page.state.records[target.id].correct, 0);
        assert.equal(page.state.records[target.id].assistedCorrect, 1);
        assert.equal(page.state.xp, 0);
        results.push({ id: target.id, entry: 'challenge_button', prompt_hints_explanation: 'PASS', assisted_record: 'PASS' });
    }
    const page = await browser();
    await page.click({ action: 'focus-subject', item: 'japanese' });
    const warmup = page.buttons().find(button => button.dataset.action === 'warmup');
    await page.click(warmup.dataset);
    await page.answer(page.state.session.questions[0], false);
    await page.click({ action: 'next' });
    assert.equal(page.state.session.score, 0);
    assert(page.html.includes('考えた時間も、きみの一歩。'));
    await page.click({ action: 'finish' });
    assert(page.html.includes('国語の続きから'));
    assert.equal(page.buttons().filter(button => button.label.includes('ものぞいてみる')).length, 4);
    await page.click({ action: 'focus-subject', item: 'social' });
    const sequence = [];
    for (let index = 0; index < 20; index++) {
        await page.click({ action: 'stretch-start', item: 'social' });
        sequence.push(page.state.session.ids[0]);
        await page.click({ action: 'stretch-solution' });
        await page.click({ action: 'next' });
        await page.click({ action: 'finish' });
    }
    assert.equal(new Set(sequence.slice(0, 7)).size, 7);
    assert(sequence.slice(1).every((id,index)=>id!==sequence[index]), 'Adjacent repetition');
    const reloaded=await browser(page.state);
    await reloaded.click({action:'stretch-start',item:'social'});
    assert.notEqual(reloaded.state.session.ids[0],sequence.at(-1));
    assert(Number.isFinite(page.state.records[sequence.at(-1)].lastAt));
    const result = {
        source_base_commit: manifest.base_source_commit, content_draft: 'app_review/v3; separately patched app code v5',
        method: 'Actual runtime handlers with simulated DOM/storage; no student trial', random_seed: seedValue,
        runtime_files_hash_checked: checkedFiles, revised_normal_cases: revisedNormal.length,
        challenge_cases: challengeBank.length, checked_cases: results,
        beginner_flow: { japanese_continues_after_wrong: true, other_subjects: 4, reassuring_message: true },
        same_day_challenge_sequence: sequence,
        known_issue_same_question_after_cycle: sequence.slice(1).some((id,index)=>id===sequence[index]),
        reload_previous_id_preserved: true,
    };
    fs.writeFileSync(path.join(output, 'learning_simulation_results.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify({ files: checkedFiles, revised_normal_cases: revisedNormal.length,
        challenge_cases: challengeBank.length, same_day_challenge_sequence: sequence }, null, 2));
}

main().catch(error => { console.error(error); process.exitCode = 1; });
