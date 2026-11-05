"""Package the actual browser runtime with draft content for read-only audit reproduction."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'reports/app_review/v3'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('site_checkout', type=Path)
    arguments = parser.parse_args()
    site = arguments.site_checkout.resolve()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=site, text=True).strip()
    if commit != 'b54cc88b362ee144a2ba013d920ed8bf41b4083a':
        raise ValueError('Use the pinned app source commit b54cc88b362ee144a2ba013d920ed8bf41b4083a')
    if subprocess.check_output(['git', 'status', '--porcelain', '--', 'dist'], cwd=site, text=True).strip():
        raise ValueError('App dist contains uncommitted changes')
    items = json.loads((OUTPUT / 'review_items.json').read_text(encoding='utf-8'))
    replacements = {}
    for item in items:
        replacements.setdefault(item['source_file'], {})[item['question']['id']] = item['question']
    files = {str(path.relative_to(site)).replace('\\', '/'): path.read_bytes()
             for path in sorted((site / 'dist').rglob('*')) if path.is_file()}
    baseline_hashes = {path: hashlib.sha256(content).hexdigest() for path, content in files.items()}
    for filename, updates in replacements.items():
        questions = json.loads(files[filename])
        revised = [updates.pop(question['id'], question) for question in questions]
        revised.extend(updates.values())
        files[filename] = (json.dumps(revised, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    manifest = {
        'base_source_commit': commit,
        'purpose': 'Local audit runtime using draft v3 app questions. No production deployment.',
        'baseline_sha256': baseline_hashes,
        'draft_sha256': {path: hashlib.sha256(content).hexdigest() for path, content in files.items()},
        'draft_question_count': len(items),
        'draft_source': 'reports/app_review/v3/review_items.json',
    }
    with zipfile.ZipFile(OUTPUT / 'audit_runtime.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files.items():
            entry = zipfile.ZipInfo(filename, date_time=(2026, 11, 5, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, content)
        entry = zipfile.ZipInfo('source-manifest.json', date_time=(2026, 11, 5, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(entry, json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (OUTPUT / 'runtime_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'files': len(files), 'draft_questions': len(items), 'zip_bytes': (OUTPUT / 'audit_runtime.zip').stat().st_size}))


if __name__ == '__main__':
    main()
