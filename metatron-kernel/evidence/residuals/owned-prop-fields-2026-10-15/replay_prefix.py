from pathlib import Path
import json,os,subprocess,sys
relative=Path('metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json')
paths=[p/relative for p in Path(__file__).resolve().parents]+[p/'nucleus'/relative for p in Path(__file__).resolve().parents]
base=json.loads(next(p for p in paths if p.is_file()).read_text())
env={k:v for k,v in os.environ.items() if not k.startswith('NUCLEUS_')}
env.update({'NUCLEUS_EXPERIMENTAL_'+x:'1' for x in base['origin_flags']});env['NUCLEUS_TRACE_DOWNSTREAM']='1';env['NUCLEUS_TRACE_PROP_SINGLETON']='1'
p=subprocess.run([str(Path(sys.argv[1]).resolve())],input=Path(__file__).with_name('prefix.ndjson').read_bytes(),capture_output=True,env=env,timeout=180)
print((p.stderr+p.stdout).decode())
assert p.returncode==0, f'Valid complete WellFounded declaration prefix must ACCEPT, got {p.returncode}'
