'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function main() {
    const [runtime, previous, vocabularyFile] = process.argv.slice(2).map(p=>path.resolve(p));
    const dist = path.join(runtime, 'dist');
    const load = p => JSON.parse(fs.readFileSync(p,'utf8'));
    const catalog = load(path.join(dist,'data/catalog.json'));
    const baseline = load(path.join(previous,'dist/data/catalog.json'));
    const Content = require(path.join(dist,'content.js'));
    const Generators = require(path.join(dist,'generators.js'));
    const bundled = JSON.parse(fs.readFileSync(path.join(runtime,'manabi_exam.html'),'utf8')
        .match(/const classroomAssets=([^\n]+);\n/)[1]);
    assert.deepEqual(bundled.data['data/catalog.json'],catalog);
    Content.validateCatalog(catalog);
    const bank = new Map();
    for(const u of catalog.units) for(const pack of u.packs) {
        const list = load(path.join(dist,pack.file));
        assert.deepEqual(bundled.data[pack.file],list,pack.file);
        for(const q of Content.validatePack(list,u,pack)){
            assert(!bank.has(q.id),q.id);
            bank.set(q.id,q);
            const correct = q.type==='text'?q.answers[0]:q.answer;
            const wrong = q.type==='choice'?(q.answer+1)%q.choices.length:q.type==='number'?q.answer+10000:'__wrong__';
            assert(Content.judge(q,correct) && !Content.judge(q,wrong),q.id);
        }
    }
    for(const u of catalog.units) assert(u.packs.reduce((count, pack)=>count+pack.count,0)>=20,u.id);
    for(const u of baseline.units) for(const p of u.packs)
        assert.deepEqual(fs.readFileSync(path.join(previous,'dist',p.file)),fs.readFileSync(path.join(dist,p.file)));
    for(const source of load(vocabularyFile)){
        const q=bank.get(source.id);
        assert.equal(q.grade,source.grade);
        assert.equal(q.prompt,source.prompt);
        assert.deepEqual(q.choices,source.choices);
        assert.equal(q.answer,source.correct_index);
        assert.equal(q.explanation,source.explanation);
    }
    const sections=catalog.examSections;
    assert.equal(new Set(sections.map(s=>s.id)).size,sections.length);
    assert.equal(new Set(sections.map(s=>s.subject+s.grade)).size,15);
    const modulePath=path.join(__dirname,'exam_units','ui.js');
    const context=vm.createContext({Content,document:{addEventListener(){}}});
    vm.runInContext(fs.readFileSync(modulePath,'utf8'),context);
    const sample=context.examSample;
    const store=Content.createStore(catalog,async p=>({ok:true,json:async()=>bundled.data[p.split('?')[0]]}));
    for(const s of sections) {
        assert(s.ids.length>=20,s.id);
        assert.equal(new Set(s.ids).size,s.ids.length,s.id);
        assert(s.ids.every(id=>bank.get(id)?.subject===s.subject && bank.get(id)?.grade===s.grade),s.id);
        for(const n of [5,20]){
            const picked=sample([s],n,{},()=>0.31);
            assert.equal(picked.length,n,s.id);
            assert.equal(new Set(picked.map(q=>q.id)).size,n,s.id);
            const questions=await store.byIds(picked.map(q=>q.id));
            assert(questions.every(q=>s.ids.includes(q.id)),s.id);
            for(const q of questions) assert(Generators.materialize(q,()=>0.31).prompt);
        }
    }
    const mixed=sections.filter(s=>s.grade===2 && s.subject==='science' && s.chapter==='電流とその利用');
    const picked=sample(mixed,20,{},()=>0.31);
    assert.equal(new Set(picked.map(q=>q.id)).size,20);
    for(const s of mixed) assert.equal(picked.filter(x=>x.section===s.id).length,4);
    const report={sections:sections.length,min:Math.min(...sections.map(s=>s.ids.length)),
        uniqueQuestions:bank.size,scoringChecks:bank.size*2,preservedLegacyQuestions:4323,
        importedJapaneseExact:1040,mixedElectricitySections:mixed.length,allSectionsSampledAt:[5,20]};
    fs.writeFileSync(path.join(runtime,'verification.json'),JSON.stringify(report,null,2)+'\n');
    console.log(report);
}
main().catch(error=>{console.error(error);process.exitCode=1});
