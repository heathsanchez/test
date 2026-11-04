"""Require exact named integration-test outcome parity, not just matching counts."""
from pathlib import Path
import os,json,subprocess,re,time,hashlib
R=Path('/workspace/scratch/38cabe96376f');A=R/'nucleus-tournaments/native-aggregate';P=R/'nucleus-tournaments/receipts/neutral-proof';info=json.loads((A/'binary.json').read_text());b=Path(info['path']);assert hashlib.sha256(b.read_bytes()).hexdigest()==info['sha256'];q=json.loads((P/'qualification.json').read_text())['candidate'];e={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};e.update(q['configuration']);e['NUCLEUS_FROZEN196']='/tmp/current208/inputs';out=A/'parity';out.mkdir(exist_ok=True)
pattern=re.compile(r'^test (\S+)(?: - should panic)? \.\.\. (ok|FAILED|ignored)',re.M)
def tests(text):return dict(pattern.findall(text))
listing=subprocess.run([str(b),'--list'],env=e,capture_output=True,text=True,check=True).stdout
all_names=[x[:-6]for x in listing.splitlines()if x.endswith(': test')];rows=[];start=time.monotonic()
for module in info['modules']:
 expected=tests((P/'candidate'/('native-'+module+'-test.log')).read_text());listed={x[len(module)+2:]for x in all_names if x.startswith(module+'::')};assert listed==set(expected),(module,'listing mismatch',listed^set(expected))
 with(out/(module+'.stdout')).open('wb')as stdout,(out/(module+'.stderr')).open('wb')as stderr:r=subprocess.run([str(b),module+'::','--include-ignored','--test-threads=1'],env=e,stdout=stdout,stderr=stderr,timeout=240)
 raw=tests((out/(module+'.stdout')).read_text());assert all(x.startswith(module+'::')for x in raw),('filter collision',module)
 actual={x[len(module)+2:]:v for x,v in raw.items()};ok=actual==expected;row=dict(module=module,rc=r.returncode,identity_and_outcome_parity=ok,tests=len(actual),expected_tests=len(expected),failures=[x for x,v in actual.items()if v=='FAILED']);rows.append(row);print(json.dumps(row),flush=True)
 (A/'parity.json').write_text(json.dumps(dict(status='WARRANTED_NAMED_INTEGRATION_TEST_PARITY'if all(x['identity_and_outcome_parity']for x in rows)and len(rows)==len(info['modules'])else'CANDIDATE',baseline_binary=q['binary_sha'],baseline_source_manifest='31ca773c4e56569c83ceadc225a61c49275f2cd706c5399e22056ee88582e780',aggregate_binary=info['sha256'],separate_module_processes=True,configuration=q['configuration'],modules=rows,wall=time.monotonic()-start),indent=2))
 assert ok,(module,expected,actual)
