"""Overlay v4 content onto a separately prepared app-code-v4 audit runtime."""
import argparse,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('runtime_base',type=Path);p.add_argument('output',type=Path);a=p.parse_args();base=a.runtime_base.resolve();out=a.output.resolve()
if base==out:raise ValueError('Use a separate output, preserving the code runtime')
if 'previousId' not in (base/'dist/strengths.js').read_text():raise ValueError('Prepare the separate strengths-v4 code branch first')
shutil.copytree(base,out,dirs_exist_ok=True)
items=json.loads((R/'reports/app_review/v4/review_items.json').read_text());groups={}
for item in items:groups.setdefault(item['source_file'],{})[item['question']['id']]=item['question']
for filename,updates in groups.items():
 f=out/filename;data=json.loads(f.read_text());data=[updates.pop(q['id'],q) for q in data];data.extend(updates.values());f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
m=json.loads((out/'source-manifest.json').read_text());m['content_draft']='social-v4/app_review-v4';m['draft_question_count']=len(items);m['draft_sha256']={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((out/'dist').rglob('*')) if f.is_file()};(out/'source-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(str(out))
