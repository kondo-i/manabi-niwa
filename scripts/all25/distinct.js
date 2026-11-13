// Keep the displayed prompts distinct even when two numeric generators draw the same values.
function distinctQuizQuestions(questions, rng = Math.random) {
    const promptKey = q => q.prompt.normalize('NFKC').replace(/\s+/g,'');
    const baseKeys = new Set(questions.map(promptKey));
    const used = new Set();
    return questions.map(q => {
        let candidate = q;
        if (q.generator && !q.variant) {
            for (let attempt = 0; attempt < 20; attempt++) {
                candidate = Generators.materialize(q,rng);
                const key = promptKey(candidate);
                if (!used.has(key) && !baseKeys.has(key)) break;
                candidate = q;
            }
        }
        const key = promptKey(candidate);
        if (used.has(key)) throw Error('同じ問題が重なりました。もう一度選んでください');
        used.add(key);
        return candidate;
    });
}
