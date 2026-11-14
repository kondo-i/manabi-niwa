'use strict';

// Real Chromium checks. App actions use clicks/inputs; evaluate only reads answers,
// storage, and geometry. The browser clock simulates a return on the following day.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const runtime = path.resolve(process.argv[2] || '/tmp/manabi-all25');
const output = path.resolve(process.argv[3] || path.join(runtime, 'browser'));
fs.mkdirSync(output, { recursive: true });
const report = { browser: 'Chromium', realIPhone: false, transport: 'localhost HTTP, single bundled HTML',
    fileProtocol: {}, scenarios: [], errors: [], layout: [] };
const html = fs.readFileSync(path.join(runtime, 'manabi_25.html'));

async function main() {
    const server = http.createServer((req, res) => {
        if (req.url.split('?')[0] !== '/manabi_25.html') {
            res.writeHead(404); res.end(); return;
        }
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(html);
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    server.unref();
    const url = `http://127.0.0.1:${server.address().port}/manabi_25.html`;
    const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
        headless: true, args: ['--no-sandbox'] });
    report.browserVersion = browser.version();
    try {
        const filePage = await browser.newPage();
        try {
            await filePage.goto(pathToFileURL(path.join(runtime, 'manabi_25.html')).href);
            await filePage.waitForSelector('aside [data-page="subjects"]');
            report.fileProtocol = { opened: true };
        } catch (error) {
            report.fileProtocol = { opened: false, reason: error.message.split('\n')[0],
                limitation: 'Managed Chromium policy blocks file URLs. Local HTTP checks the exact same HTML bytes.' };
        }
        await filePage.close();
        for (const viewport of [{ width: 375, height: 812 }, { width: 1280, height: 900 }]) {
            const tag = `${viewport.width}px`;
            const context = await browser.newContext({ viewport, timezoneId: 'UTC' });
            const page = await context.newPage();
            const externalRequests = [];
            const popups = [];
            page.on('pageerror', e => report.errors.push({ viewport: tag, error: e.message }));
            page.on('popup', p => popups.push(p));
            page.on('request', req => { if (!req.url().startsWith(url.split('/manabi_25.html')[0]) && !req.url().startsWith('data:')) externalRequests.push(req.url()); });
            await page.clock.install({ time: new Date('2026-11-13T12:00:00Z') });
            page.setDefaultTimeout(10000);
            const snapshot = async name => {
                const geometry = await page.evaluate(() => ({ viewport: innerWidth,
                    document: document.documentElement.scrollWidth,
                    overflowing: [...document.querySelectorAll('#app *')].filter(e => {
                        const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1);
                    }).slice(0, 10).map(e => ({ element: e.tagName, className: e.className, text: e.textContent.slice(0, 80) })) }));
                report.layout.push({ viewport: tag, screen: name, ...geometry });
                await page.screenshot({ path: path.join(output, `${tag}-${name}.png`) });
            };
            const selectMenu = async (subject, grade) => {
                await page.locator('aside [data-page="subjects"]').click();
                await page.locator(`#app [data-subject="${subject}"]`).click();
                await page.locator(`#app [data-grade="${grade}"]`).click();
                assert(!(await page.locator('#app').innerText()).includes('準備中'));
            };
            const normalMenu = async () => {
                await selectMenu('science', 3);
                assert(await page.locator('[data-action="practice25"][data-unit="all25-motion-data"]').isVisible());
            };
            const solve = async (count, wrongFirst = false, shot = '') => {
                const ids = [], prompts = [];
                for (let i = 0; i < count; i++) {
                    await page.locator('.question').waitFor();
                    const q = await page.evaluate(() => {
                        const q = state.session.questions[state.session.index];
                        return { id: q.id, type: q.type, answer: q.type === 'text' ? q.answers[0] : q.answer,
                            choiceCount: q.choices?.length, explanation: q.explanation };
                    });
                    ids.push(q.id);
                    prompts.push((await page.locator('.question').innerText()).normalize('NFKC').replace(/\s+/g, ''));
                    for (const image of await page.locator('.question-figure img').all()) {
                        await image.waitFor();
                        assert(await image.evaluate(img => img.complete && img.naturalWidth > 0), 'Question image must load');
                        assert.match(await image.getAttribute('src'), /^data:image\//, 'Single HTML must embed question figures');
                        assert.match(await page.locator('.question-figure a').getAttribute('href'), /^data:image\//,
                            'Figure enlargement link must also be embedded');
                        await image.scrollIntoViewIfNeeded();
                        await snapshot(`${q.id}-figure`);
                        await page.locator('.question-figure a').click();
                        const dialog = page.getByRole('dialog', { name: '図を拡大' });
                        await dialog.waitFor();
                        assert(await dialog.locator('img').evaluate(img => img.complete && img.naturalWidth > 0),
                            'Enlarged figure must load in the same-page dialog');
                        assert.match(await dialog.locator('img').getAttribute('src'), /^data:image\//);
                        assert.equal(await dialog.locator('p').innerText(), await image.getAttribute('alt'));
                        await snapshot(`${q.id}-enlarged`);
                        await dialog.getByRole('button', { name: '閉じる' }).click();
                        await dialog.waitFor({ state: 'detached' });
                        assert.equal((await page.locator('.question').innerText()).normalize('NFKC').replace(/\s+/g, ''), prompts.at(-1));
                        assert(await page.locator('.question-figure a').evaluate(link => document.activeElement === link),
                            'Closing the figure must return focus to the original link');
                    }
                    const wrong = wrongFirst && i === 0;
                    const answer = wrong ? q.type === 'choice' ? (q.answer + 1) % q.choiceCount : q.type === 'number' ? Number(q.answer) + 10000 : '__wrong__' : q.answer;
                    if (q.type === 'choice') await page.locator(`[data-answer="${answer}"]`).click();
                    else {
                        await page.locator('#answer-value').fill(String(answer));
                        await page.locator('#typed-answer button[type="submit"], #typed-answer button.primary').first().click();
                    }
                    const feedback = page.locator('.explain');
                    await feedback.waitFor();
                    assert.equal(await feedback.locator('p').first().innerText(), q.explanation);
                    assert.match(await feedback.locator('b').innerText(), wrong ? /いっしょに確かめよう/ : /正解/);
                    if (i === 0 && shot) await snapshot(shot);
                    await page.locator('[data-action="next"]').click();
                }
                await page.locator('.score').waitFor();
                assert.equal(new Set(ids).size, count);
                assert.equal(new Set(prompts).size, count);
                assert.equal((await page.locator('.score').innerText()).replace(/\s+/g, ''), `${count - Number(wrongFirst)}/${count}`);
                return ids;
            };
            await page.goto(url);
            await normalMenu();
            await snapshot('normal-menu');
            await page.locator('[data-action="practice"][data-unit="all25-motion-data"]').click();
            await solve(5, false, 'five-feedback');
            report.scenarios.push({ viewport: tag, mode: 'normal5', unit: 'all25-motion-data', score: '5/5' });
            await page.locator('[data-action="finish"]').click();

            for (const [subject, grade, unit] of [
                ['math', 1, 'repair-math-g1-primes'],
                ['english', 2, 'repair-english-g2-obligation'],
                ['science', 3, 'repair-science-g3-data'],
                ['japanese', 2, 'repair-japanese-g2-conjugation'],
            ]) {
                await selectMenu(subject, grade);
                const start = page.locator(`[data-action="practice25"][data-unit="${unit}"]`);
                if (!await start.count()) continue; // Also supports reproducing the pinned baseline.
                await start.click();
                await solve(25, false, `${unit}-feedback`);
                report.scenarios.push({ viewport: tag, mode: 'newUnit25', unit, score: '25/25' });
                if (unit === 'repair-japanese-g2-conjugation') await snapshot(`${unit}-results`);
                await page.locator('[data-action="finish"]').click();
                if (unit === 'repair-japanese-g2-conjugation') {
                    await selectMenu(subject, grade);
                    await page.locator('[data-action="exam-from-units"]').click();
                    const checkbox = page.locator(`[data-exam-section="${unit}"]`);
                    const title = await checkbox.locator('..').locator('span').innerText();
                    await checkbox.check();
                    assert.match(await page.locator('.exam-start strong').innerText(), /1小単元/);
                    await snapshot(`${unit}-exam-selection`);
                    await page.locator('[data-action="exam-start"][data-size="25"]').click();
                    await solve(25, false, `${unit}-exam-feedback`);
                    assert.equal(await page.locator('.exam-results p').count(), 1);
                    const result = await page.locator('.exam-results p').innerText();
                    assert(result.includes(title));
                    assert.match(result, /25\s*\/\s*25問/);
                    await snapshot(`${unit}-exam-results`);
                    report.scenarios.push({ viewport: tag, mode: 'newUnitExam25', unit,
                        score: '25/25', perUnit: [result] });
                    await page.locator('[data-action="exam-return"]').click();
                    assert.match(await page.locator('.exam-start strong').innerText(), /1小単元/);
                    assert(await checkbox.isChecked());
                    await selectMenu(subject, grade);
                    assert(await page.locator(`[data-action="practice25"][data-unit="${unit}"]`).isVisible());
                }
            }

            await normalMenu();
            await page.locator('[data-action="exam-from-units"]').click();
            for (const id of ['all25-forces', 'all25-motion-data', 'all25-power']) {
                await page.locator(`[data-exam-section="${id}"]`).check();
            }
            await snapshot('exam-selection');
            await page.locator('[data-action="exam-start"][data-size="25"]').click();
            await solve(25);
            assert.match(await page.locator('.exam-results').innerText(), /小単元別の結果/);
            assert.equal(await page.locator('.exam-results p').count(), 3);
            const results = await page.locator('.exam-results p').allTextContents();
            const totals = results.map(t => Number(t.match(/\/\s*(\d+)問/)[1])).sort((a, b) => a - b);
            assert.deepEqual(totals, [8, 8, 9]);
            await snapshot('exam-results');
            report.scenarios.push({ viewport: tag, mode: 'mixedExam25', score: '25/25', perUnit: results });
            await page.locator('[data-action="exam-return"]').click();
            assert.match(await page.locator('.exam-start strong').innerText(), /3小単元/);

            await normalMenu();
            await page.locator('[data-action="practice25"][data-unit="all25-motion-data"]').click();
            const ids = await solve(25, true, 'wrong-feedback');
            await snapshot('normal25-results');
            assert.match(await page.locator('#app').innerText(), /解説を読んで、明日また練習しよう/);
            await page.locator('#app [data-page="review"]').click();
            assert.match(await page.locator('#app').innerText(), /復習待ち 1問/);
            const beforeReload = await page.evaluate(id => JSON.parse(localStorage.getItem('kondo-study-lab-v1')).records[id], ids[0]);
            assert.equal(beforeReload.lastCorrect, false);
            assert.equal(beforeReload.lastDate, '2026-11-13');
            await page.clock.setFixedTime(new Date('2026-11-14T12:00:00Z'));
            await page.reload();
            await page.locator('aside [data-page="review"]').click();
            await snapshot('next-day-review');
            await page.locator('[data-action="review"][data-unit="all25-motion-data"]').click();
            await solve(1);
            await page.locator('[data-action="finish"]').click();
            await page.locator('aside [data-page="review"]').click();
            assert.match(await page.locator('#app').innerText(), /復習待ちはありません/);
            const afterReview = await page.evaluate(id => JSON.parse(localStorage.getItem('kondo-study-lab-v1')).records[id], ids[0]);
            assert.equal(afterReview.lastCorrect, true);
            assert.equal(afterReview.lastDate, '2026-11-14');
            report.scenarios.push({ viewport: tag, mode: 'normal25AndNextDayReview', score: '24/25',
                reviewedQuestion: ids[0], resultsReviewLink: true, storageSurvivedReload: true,
                wrongDate: beforeReload.lastDate, reviewDate: afterReview.lastDate });
            assert.deepEqual(externalRequests, [], 'Bundled HTML must work without external resources');
            assert.equal(popups.length, 0, 'Figure enlargement must stay on the current page');
            await context.close();
        }
        assert.equal(report.errors.length, 0, 'JavaScript page errors');
        const overflow = report.layout.filter(x => x.document > x.viewport + 1);
        report.horizontalOverflow = overflow;
        assert.equal(overflow.length, 0, 'Horizontal overflow; inspect layout entries');
        report.passed = true;
    } finally {
        await browser.close();
        server.close();
    }
}
main().catch(error => { report.passed = false; report.failure = error.stack; process.exitCode = 1; })
    .finally(() => { fs.writeFileSync(path.join(output, 'browser-verification.json'), JSON.stringify(report, null, 2) + '\n');
        console.log(JSON.stringify({ passed: report.passed, fileProtocol: report.fileProtocol, scenarios: report.scenarios.length, report: path.join(output, 'browser-verification.json'), failure: report.failure?.split('\n')[0] })); });
