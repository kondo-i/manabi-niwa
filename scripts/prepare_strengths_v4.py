"""Rebuild a local audit runtime from the pinned v3 ZIP + three reviewed code patches."""
import argparse,hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/'reports/app_review/v3/audit_runtime.zip') as z:
 for info in z.infolist():
  target=(out/info.filename).resolve()
  if not target.is_relative_to(out):raise ValueError('Unsafe archive path')
  if info.is_dir():target.mkdir(parents=True,exist_ok=True)
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
manifest=json.loads((out/'source-manifest.json').read_text());manifest['code_patch_base']='fea74f767cd2467a2eda897a4ddc6cd4e7f371f3 v3 audit runtime';manifest['code_patch_purpose']='same-day challenge non-repetition; no deployment'
for name in ['strengths.js','strength-ui.js','app.js']:
 target=out/'dist'/name;target.write_bytes((R/'app_drafts/strengths-v4'/name).read_bytes())
manifest['draft_sha256']={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((out/'dist').rglob('*')) if f.is_file()}
(out/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(str(out))
