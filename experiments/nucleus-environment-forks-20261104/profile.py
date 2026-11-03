"""Software CPU sampling of the exact qualified kernel, with no score claim."""
import glob
import hashlib
import json
import os
from pathlib import Path
import subprocess

OUT=Path('/tmp/nucleus-cost-profile')
OUT.mkdir(exist_ok=True)
prior=Path('/tmp/nonzero-qualified')
q=json.loads((prior/'qualification.json').read_text())['candidate']
assert q['qualified']and q['binary_sha']=='013e742dc3bf541301235b6e6d37615b62c9800b923b7c9506b254cffdbfe61e'
binary=prior/'candidate/nucleus'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==q['binary_sha']
binary.chmod(0o755)
env=q['configuration']|{'NUCLEUS_TRACE_DOWNSTREAM':'1'}
tools=glob.glob('/usr/lib/linux-tools/*/perf')
perf=sorted(tools)[-1]if tools else '/usr/bin/perf'
records=[]
for label,source,sha in [('prefix',Path('/tmp/profile-prefix.ndjson'),'f37e9434b2cee5f9623a2218fb6418c58d43dbe5ac3582cadd9cc844dfa215b4'),('full',Path('/tmp/mathlib.ndjson'),'22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6')]:
    with source.open('rb')as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    assert actual==sha
    data=OUT/(label+'.perf.data')
    command=['/usr/bin/sudo','-E',perf,'record','-e','cpu-clock:u','-F','99','--call-graph','dwarf,16384','-o',str(data),'--',str(binary)]
    with source.open('rb')as stream:
        result=subprocess.run(command,stdin=stream,capture_output=True,env=env,timeout=300)
    (OUT/(label+'.stdout')).write_bytes(result.stdout)
    (OUT/(label+'.stderr')).write_bytes(result.stderr)
    terminal=[line for line in result.stderr.decode(errors='replace').splitlines()if line.startswith('NUCLEUS_DOWNSTREAM:')]
    passed=result.returncode==2 and terminal and 'Lean.Data.AC.EvalInformation'in terminal[-1]and data.exists()
    records.append(dict(case=label,input_sha256=sha,binary_sha256=q['binary_sha'],rc=result.returncode,terminal=terminal[-1]if terminal else None,profile_completed=bool(passed)))
    if passed:
        subprocess.run(['/usr/bin/sudo','/bin/chmod','a+r',str(data)],check=True)
        for mode,args in [('self',['--no-children']),('callers',['--children'])]:
            report=subprocess.run(['/usr/bin/sudo',perf,'report','--stdio','--percent-limit','0.2','-i',str(data),*args],capture_output=True,env=env,timeout=60)
            (OUT/(label+'-'+mode+'.txt')).write_bytes(report.stdout+report.stderr)
            assert report.returncode==0
    (OUT/'report.json').write_text(json.dumps(dict(status='DIAGNOSTIC_ONLY',method='software-cpu-clock-sampling',no_instruction_or_rank_claim=True,records=records),indent=2)+'\n')
    assert passed,'No profile claim without the exact known terminal boundary'
