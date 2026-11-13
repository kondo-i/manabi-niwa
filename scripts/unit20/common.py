from hashlib import sha256


def choice(prompt, answer, wrong_a, wrong_b, explanation, transcript=None):
    options = [answer, wrong_a, wrong_b]
    assert len(set(options)) == 3, (prompt, options)
    shift = sha256(prompt.encode()).digest()[0] % 3
    item = dict(type='choice', prompt=prompt, choices=options[shift:] + options[:shift],
                answer=(-shift) % 3, explanation=explanation)
    if transcript:
        item['transcript'] = transcript
    return item


def number(prompt, answer, explanation, tolerance=1e-9):
    return dict(type='number', prompt=prompt, answer=answer, tolerance=tolerance, explanation=explanation)


def word(prompt, answer, explanation, english=False):
    item = dict(type='text', prompt=prompt, answers=answer.split('/'), explanation=explanation)
    if english:
        item['caseInsensitive'] = True
    return item


def cards(rows):
    return [choice(*line.split('|')) for line in rows.strip().splitlines() if line.strip()]


def rotating(items, index):
    return items[index % len(items)]
