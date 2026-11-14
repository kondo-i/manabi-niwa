from pathlib import Path
import hashlib,json,subprocess,concurrent.futures
base='https://kondo-study-lab.vast-stone-7426.chatgpt.site'
local=Path('/workspace/manabi-site/dist');out=Path('/workspace/manabi-delivery/live-20261114');out.mkdir(exist_ok=True)
files=['index.html','release.json','data/catalog.json','app.js','content.js','data/packs/repair-science-g3-buoyancy-p1.json','data/packs/repair-math-g2-boxplots-p1.json','data/packs/japanese-g2-auxiliary-context-balance-001.json','data/figures/buoyancy-forces.svg','data/figures/boxplot-reading.svg','data/figures/boxplot-scores.svg','data/figures/boxplot-waiting.svg','data/figures/boxplot-same.svg']
def check(f):
 p=out/f;p.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','-fsSL','--compressed','--max-time','30',base+'/'+f,'-o',str(p)],check=True)
 expected=hashlib.sha256((local/f).read_bytes()).hexdigest();actual=hashlib.sha256(p.read_bytes()).hexdigest()
 assert actual==expected,f
 return {'file':f,'sha256':actual,'matches_promoted_source':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as x:results=list(x.map(check,files))
c=json.loads((out/'data/catalog.json').read_text());release=json.loads((out/'release.json').read_text())
assert len(c['units'])==347 and len(c['examSections'])==276 and release['unique_questions']==8848
for uid in ['repair-science-g3-buoyancy','repair-math-g2-boxplots']:
 s=next(s for s in c['examSections'] if s['id']==uid)
 assert len(s['ids'])==25
report={'url':base,'status':'verified by native deployment and HTTP file reads','version_number':25,'site_source_sha':'2514cc015ebe4cf38775e08cf2a01174666a4b40','curriculum_source_sha':'387e03a7518a0ab6c0af780464bdc4942e4d71cd','regular_units':347,'exam_sections':276,'question_ids':8848,'files_verified':results,'browser_qa':False,'iphone_qa':False}
(out/'live_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files_verified'},ensure_ascii=False))
