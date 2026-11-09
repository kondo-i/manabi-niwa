"""Assemble a local-only prototype: pinned runtime, reviewed v5 code, v4 items, new drafts."""
import argparse,collections,hashlib,json,subprocess,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();out=a.output.resolve()
if out.exists() and any(out.iterdir()):raise ValueError('Choose an empty output directory')
subprocess.run([sys.executable,str(R/'scripts/prepare_strengths_v5.py'),str(out)],check=True)
items=json.loads((R/'data/release_prep/review_items_v4.json').read_text());groups={}
for item in items:groups.setdefault(item['source_file'],{})[item['question']['id']]=item['question']
for filename,updates in groups.items():
 f=out/filename;data=json.loads(f.read_text());data=[updates.pop(q['id'],q) for q in data];data.extend(updates.values());f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
qs=json.loads((R/'data/expansion/v1/questions.json').read_text());units={}
for q in qs:units.setdefault(q['unitId'],[]).append(q)
catalog_path=out/'dist/data/catalog.json';catalog=json.loads(catalog_path.read_text())
for uid,questions in sorted(units.items()):
 q=questions[0];packid=uid+'-pack';filename='data/packs/'+packid+'.json';pack=[]
 for item in questions:
  x={k:v for k,v in item.items() if k not in ['oracle','family','auditStatus','curriculumTopic']};pack.append(x)
 data=(json.dumps(pack,ensure_ascii=False,indent=2)+'\n').encode();(out/'dist'/filename).write_bytes(data)
 catalog['units'].append({'id':uid,'subject':q['subject'],'grade':q['grade'],'title':'【試作】'+q['unitTitle'],'description':'制作側の検証用。内容監査・単元網羅の認定前。問題数は数値違いの練習を含む。','status':'prototype' if len(pack)>=5 else 'draft','packs':[{'id':packid,'file':filename,'revision':hashlib.sha256(data).hexdigest()[:12],'count':len(pack),'legacyIds':[x['id'] for x in pack],'randomized':False}]})
catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
html=out/'dist/index.html';text=html.read_text();text=text.replace('<body>','<body><div style="padding:10px;background:#fff0b8;color:#332b13;text-align:center">制作確認用・未公開：追加教材は試作です。学習記録はこの確認環境内に保存されます。</div>',1);text=re.sub(r'試作教材：理科240問.*?先生の最終校閲は未実施です。','制作確認用：通常問題2,118問（うち5問は単元準備中）、難問28問。追加1,218問は数値違いを含む試作で、内容の最終校閲前です。',text);html.write_text(text)
manifest=json.loads((out/'source-manifest.json').read_text());manifest['content_overlay']={'source_commit':'f9aad786444ef392cf98ed2457f54f428e74b25c','review_items':len(items),'file':'data/release_prep/review_items_v4.json'};manifest['expansion']={'questions':len(qs),'families':len({q['family'] for q in qs}),'status':'prototype_not_release_approved'};manifest['draft_sha256']={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((out/'dist').rglob('*')) if f.is_file()};(out/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(out)
