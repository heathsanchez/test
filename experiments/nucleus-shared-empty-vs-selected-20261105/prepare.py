from pathlib import Path
import json,shutil,re
r=Path(__file__).resolve().parent
paths={'A':Path('/tmp/nucleus-core-completion-readback/artifact/candidate/nucleus'),'B':Path('/tmp/nucleus-shared-empty-universes/nucleus')}
import hashlib
expected={a:hashlib.sha256(p.read_bytes()).hexdigest()for a,p in paths.items()};assert expected==dict(A='72ee79b8e1757ff65b06ee37d9321315b9b113f9503cbda635e3ebe1e3b99a41',B='a6c283d705fbd3f738ae905d84f88b86dcd338c01ed958e94d5577a3e7def63a')
for a,p in paths.items():(r/a/'candidate').mkdir(parents=True);shutil.copyfile(p,r/a/'candidate/nucleus')
shutil.copyfile('/tmp/nucleus-parametric-hot-pair/hot.ndjson',r/'hot.ndjson');config=json.loads(Path('/tmp/nucleus-core-completion-readback/artifact/qualification.json').read_text())['candidate']['configuration'];assert config==json.loads(Path('/tmp/nucleus-shared-empty-universes/report.json').read_text())['configuration'];(r/'configuration.json').write_text(json.dumps(config,indent=2))
s=Path('/tmp/nucleus-core-root-tournament/run.py').read_text();s=re.sub(r'EXPECTED=.*\n','EXPECTED='+repr(expected)+'\n',s,count=1);s=s.replace("enumerate('CBAABC',1)","enumerate('BAAB',1)").replace('n<6','n<4').replace('n==6','n==4').replace("order='CBAABC'","order='BAAB'").replace("for arm in 'ABC'","for arm in 'AB'").replace("dict(A='sealed-default2003',B='completed-whole-core-conversion-runtime253',C='whole-core-plus-root-payload-runtime257')","dict(A='sealed-selected-default72ee',B='shared-empty-universe-payload-runtime261')");(r/'run.py').write_text(s)
