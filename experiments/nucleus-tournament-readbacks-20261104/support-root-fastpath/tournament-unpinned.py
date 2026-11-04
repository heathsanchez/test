"""Fresh-process ABBA replay at one exact qualified full-input frontier."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,signal,statistics,subprocess,threading,time

def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--candidate',type=Path,required=True);a.add_argument('--parent-receipt',type=Path,required=True);a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();x.out.mkdir(parents=True,exist_ok=False)
 q=json.loads((x.parent_receipt/'qualification.json').read_text())['candidate'];full=json.loads((x.parent_receipt/'full.json').read_text());assert q['qualified']and full['result']['rc']==2
 assert digest(x.baseline)==q['binary_sha'];assert digest(x.input)==full['source_sha'];assert x.input.stat().st_size==6184415052
 env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(q['configuration']);env['NUCLEUS_TRACE_DOWNSTREAM']='1';bins={}
 for name,source in [('A',x.baseline),('B',x.candidate)]:
  target=x.out/(name+'.nucleus');shutil.copyfile(source,target);target.chmod(0o555);bins[name]=target
 meta=dict(status='RUNNING',schedule=['A','B','B','A'],configuration=q['configuration'],trace_flags={'NUCLEUS_TRACE_DOWNSTREAM':'1'},input_sha=full['source_sha'],input_bytes=x.input.stat().st_size,expected_terminal=full['terminal'],binary_sha={k:digest(v)for k,v in bins.items()},parent_frontier=full['next_frontier'],cpu_affinity=sorted(os.sched_getaffinity(0)),rounds=[],full_mathlib='UNKNOWN',official_rank='UNKNOWN');save(x.out/'results.json',meta)
 for index,arm in enumerate(meta['schedule']):
  b=bins[arm];assert digest(b)==meta['binary_sha'][arm];prefix=x.out/('round-'+str(index)+'-'+arm);start=time.monotonic();cut=[]
  with x.input.open('rb')as inp,Path(str(prefix)+'.stdout').open('wb')as out,Path(str(prefix)+'.stderr').open('wb')as err:
   child=subprocess.Popen([str(b)],stdin=inp,stdout=out,stderr=err,env=env,start_new_session=True)
   def stop():
    cut.append('TIME_CUTOFF')
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   timer=threading.Timer(600,stop);timer.start();pid,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status);timer.cancel()
  lines=Path(str(prefix)+'.stderr').read_text().splitlines();term=[s for s in lines if s.startswith('NUCLEUS_DOWNSTREAM:')];terminal=term[-1]if term else None
  row=dict(index=index,arm=arm,rc=child.returncode,user=usage.ru_utime,system=usage.ru_stime,cpu=usage.ru_utime+usage.ru_stime,wall=time.monotonic()-start,rss_kib=usage.ru_maxrss,terminal=terminal,cutoff=cut,matched=child.returncode==2 and terminal==full['terminal']and not cut);meta['rounds'].append(row);save(x.out/'results.json',meta);print(json.dumps(row),flush=True)
  if not row['matched']:meta['status']='NOT_MATCHED_FRONTIER';save(x.out/'results.json',meta);return
 base=[r['cpu']for r in meta['rounds']if r['arm']=='A'];cand=[r['cpu']for r in meta['rounds']if r['arm']=='B'];meta.update(status='MATCHED_FRONTIER_SPEED_WIN'if max(cand)<min(base)*.99 else'MATCHED_FRONTIER_SLOWER'if min(cand)>max(base)*1.01 else'NO_ESTABLISHED_SPEED_WIN',baseline_median_cpu=statistics.median(base),candidate_median_cpu=statistics.median(cand),median_cpu_ratio=statistics.median(base)/statistics.median(cand),median_cpu_reduction_percent=100*(1-statistics.median(cand)/statistics.median(base)),criterion='Every observed candidate CPU must beat every baseline CPU by more than1%; two observations per arm, no statistical confidence claim');save(x.out/'results.json',meta);print(json.dumps({k:v for k,v in meta.items()if k not in ['rounds','configuration','cpu_affinity']}),flush=True)
if __name__=='__main__':main()
