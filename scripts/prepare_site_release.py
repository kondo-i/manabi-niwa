"""Promote a verified classroom runtime to the existing static Sites checkout."""
import argparse
import hashlib
import json
import re
import shutil
import tarfile
from pathlib import Path
from urllib.parse import urlsplit

PROJECT = 'appgprj_6adf49333e2081918804182bd0af840b'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('runtime', type=Path); p.add_argument('site_checkout', type=Path)
    p.add_argument('--curriculum-sha', required=True)
    args = p.parse_args()
    assert re.fullmatch('[a-f0-9]{40}', args.curriculum_sha)
    site = args.site_checkout.resolve()
    manifest = json.loads((site / '.openai/hosting.json').read_text())
    assert manifest['project_id'] == PROJECT and manifest['static']['directory'] == 'dist'
    runtime = args.runtime.resolve()
    verification = json.loads((runtime / 'verification.json').read_text())
    quality = json.loads((runtime / 'quality.json').read_text())
    assert quality['publication_delta_acceptance'] == 'passed'
    assert verification['uniqueQuestions'] == quality['all_questions']['question_ids']
    target = site / 'dist'
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(runtime / 'dist', target)
    index = target / 'index.html'
    text = index.read_text()
    text = re.sub(r'\?v=[^"\s]+', '?v=20261114-' + args.curriculum_sha[:12], text)
    text = text.replace('</footer>', '<br>教材更新：2026年11月14日</footer>')
    index.write_text(text)
    release = dict(date='2026-11-14', curriculum_source_sha=args.curriculum_sha,
                   unique_questions=verification['uniqueQuestions'],
                   regular_units=verification['regular25'], exam_sections=verification['exam25'],
                   student_html_sha256=digest(runtime / 'manabi_25.html'))
    (target / 'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
    # Read every pack and all entrypoint resources from the promoted tree.
    catalog = json.loads((target / 'data/catalog.json').read_text())
    ids = []
    for u in catalog['units']:
        for pack in u['packs']:
            qs = json.loads((target / pack['file']).read_text())
            assert len(qs) == pack['count']
            ids.extend(q['id'] for q in qs)
    assert len(ids) == len(set(ids)) == release['unique_questions']
    for ref in re.findall(r'(?:src|href)="([^"]+)"', text):
        parsed = urlsplit(ref)
        if parsed.scheme or not parsed.path or parsed.path.startswith('#'): continue
        assert (target / parsed.path).is_file(), ref
    for f in (runtime / 'dist').rglob('*'):
        if f.is_file() and f.name != 'index.html':
            assert digest(f) == digest(target / f.relative_to(runtime / 'dist'))
    (site / 'release-provenance.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(release,ensure_ascii=False))

if __name__ == '__main__': main()
