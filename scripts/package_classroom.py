"""Package student/teacher artifacts and verify an actual ZIP extraction."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ['manabi_25.html', 'teacher_answers.csv', 'unit_counts.csv', 'unit_quality.csv',
           'summary.json', 'verification.json', 'quality.json', 'delta.json',
           'coverage_matrix.csv', 'coverage_summary.json']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('runtime', type=Path); p.add_argument('delivery', type=Path)
    p.add_argument('--report-dir', type=Path, default=ROOT / 'reports/coverage_repair')
    args = p.parse_args()
    out = args.delivery.resolve(); out.mkdir(parents=True)
    for name in EXPORTS: shutil.copyfile(args.runtime / name, out / name)
    shutil.copyfile(args.report_dir / 'README.md', out / 'README.md')
    with tempfile.TemporaryDirectory(prefix='manabi-package-') as tmp:
        bundle = Path(tmp) / 'bundle'; bundle.mkdir()
        for name in EXPORTS + ['README.md']: shutil.copyfile(out / name, bundle / name)
        shutil.copytree(args.runtime / 'dist', bundle / 'dist')
        shutil.copytree(args.report_dir, bundle / 'reports')
        files = sorted(f for f in bundle.rglob('*') if f.is_file())
        hashes = {f.relative_to(bundle).as_posix(): sha(f) for f in files}
        (bundle / 'SHA256.json').write_text(json.dumps(hashes, indent=2)+'\n')
        archive = out / 'manabi_classroom.zip'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for f in sorted(f for f in bundle.rglob('*') if f.is_file()):
                info = zipfile.ZipInfo(f.relative_to(bundle).as_posix(), (2026, 11, 13, 0, 0, 0))
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes(), compresslevel=9)
        extracted = Path(tmp) / 'extracted'
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            z.extractall(extracted)
        assert all(sha(extracted / f) == h for f, h in hashes.items())
        assert (extracted / 'manabi_25.html').is_file()
        catalog = json.loads((extracted / 'dist/data/catalog.json').read_text())
        assert all((extracted/'dist'/p['file']).is_file() for u in catalog['units'] for p in u['packs'])
        manifest = dict(zip_sha256=sha(archive), zip_bytes=archive.stat().st_size,
                        files_verified_after_extraction=len(hashes)+1, extracted_pack_paths_verified=True,
                        standalone_sha256={f:sha(out/f) for f in EXPORTS},
                        note='展開した全ファイルのハッシュ、入口HTML、catalogからの全pack参照を確認。')
        (out / 'package_verification.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(manifest,ensure_ascii=False))

if __name__ == '__main__': main()
