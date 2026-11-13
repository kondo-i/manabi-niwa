'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function main() {
    const root = path.resolve(process.argv[2]);
    const dist = path.join(root, 'dist');
    const baseline = path.resolve(process.argv[3]);
    const load = file => JSON.parse(fs.readFileSync(file, 'utf8'));
    const catalog = load(path.join(dist, 'data/catalog.json'));
    const oldCatalog = load(path.join(baseline, 'data/catalog.json'));
    const Content = require(path.join(dist, 'content.js'));
    const html = fs.readFileSync(path.join(root, 'manabi_20.html'), 'utf8');
    const assets = JSON.parse(html.match(/const classroomAssets=([^\n]+);\n/)[1]);
    const ids = new Set();
    const oldPrompts = new Set();
    const newPrompts = new Set();
    const cells = new Set();
    let total = 0;
    let added = 0;
    let audio = 0;
    const normalize = prompt => prompt.normalize('NFKC').replace(/\s+/g, '');

    for (const u of oldCatalog.units) {
        for (const pack of u.packs) {
            const prior = fs.readFileSync(path.join(baseline, pack.file));
            assert.deepEqual(fs.readFileSync(path.join(dist, pack.file)), prior, pack.file);
            JSON.parse(prior).forEach(q => oldPrompts.add(normalize(q.prompt)));
        }
    }
    Content.validateCatalog(catalog);
    assert.deepEqual(catalog.units.map(u => u.id), oldCatalog.units.map(u => u.id));
    assert.deepEqual(assets.data['data/catalog.json'], catalog);
    assert.equal(Content.readyUnits(catalog).length, catalog.units.length);
    const store = Content.createStore(catalog, async url => ({
        ok: true, json: async () => assets.data[url.split('?')[0]]
    }));
    for (const unit of catalog.units) {
        cells.add(unit.subject + unit.grade);
        assert(Content.count(unit) >= 20, unit.id);
        for (const pack of unit.packs) {
            const bank = load(path.join(dist, pack.file));
            Content.validatePack(bank, unit, pack);
            assert.deepEqual(bank, assets.data[pack.file]);
            for (const q of bank) {
                assert(!ids.has(q.id), q.id);
                ids.add(q.id);
                total++;
                const correct = q.type === 'text' ? q.answers[0] : q.answer;
                const wrong = q.type === 'choice' ? (q.answer + 1) % q.choices.length :
                    q.type === 'number' ? q.answer + 1000 : '__INVALID__';
                assert(Content.judge(q, correct), q.id);
                assert(!Content.judge(q, wrong), q.id);
                if (pack.id.endsWith('-practice20')) {
                    const p = normalize(q.prompt);
                    assert(!oldPrompts.has(p) && !newPrompts.has(p), q.id);
                    newPrompts.add(p);
                    added++;
                }
                if (q.audio) {
                    const bytes = fs.readFileSync(path.join(dist, q.audio));
                    assert(bytes.length > 1500, q.id);
                    assert.equal(assets.audio[q.audio], 'data:audio/mpeg;base64,' + bytes.toString('base64'));
                    audio++;
                }
            }
        }
        const first = await store.sample(unit.id, 5, () => 0.314);
        assert.equal(new Set(first.map(q => q.id)).size, 5);
        const records = Object.fromEntries(first.map(q => [q.id, { attempts: 1, packId: q.packId }]));
        const second = await store.sample(unit.id, 5, () => 0.314, { records });
        assert(second.every(q => !records[q.id]), unit.id);
        const all = await store.sample(unit.id, 20, () => 0.314);
        assert.equal(new Set(all.map(q => q.id)).size, 20);
        assert(all.every(q => q.unitId === unit.id));
    }
    assert.equal(cells.size, 15);
    const summary = load(path.join(root, 'unit20_summary.json'));
    assert.equal(total, summary.total);
    assert.equal(added, summary.added);
    assert.equal(added, 1967);
    const report = {
        units: catalog.units.length, questions: total, added,
        minimum: Math.min(...catalog.units.map(Content.count)),
        maximum: Math.max(...catalog.units.map(Content.count)),
        five_question_sampling_units: catalog.units.length,
        unseen_priority_units: catalog.units.length,
        twenty_question_sampling_units: catalog.units.length,
        scoring_cases: 2 * total, embedded_audio_files: audio,
        added_normalized_exact_prompt_duplicates: 0,
        existing_question_packs_byte_identical: true
    };
    const data = JSON.stringify(report, null, 2) + '\n';
    fs.writeFileSync(path.join(root, 'unit20_verification.json'), data);
    process.stdout.write(data);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
