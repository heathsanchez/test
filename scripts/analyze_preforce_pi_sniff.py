from pathlib import Path
import json, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'results/preforce-pi-v1')

def parse(path):
    c={}
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('MG_PREFORCE_PI '):
            k,v=line.split(' ',1)[1].split('=',1); c[k]=int(v)
    return c

out=[]
for p in sorted(root.glob('sniff.*.stderr')):
    tag=p.stem.split('.',1)[1]; c=parse(p); u=max(1,c.get('unify_enter',0)); pi=max(1,c.get('pi_enter',0))
    ptr_total=c.get('ptr_pre',0)+c.get('ptr_after_left',0)+c.get('ptr_after_both',0)
    rec={
      'workload':tag,'counters':c,
      'shares':{
        'ptr_pre_of_unify':c.get('ptr_pre',0)/u,
        'ptr_after_left_of_unify':c.get('ptr_after_left',0)/u,
        'ptr_after_both_of_unify':c.get('ptr_after_both',0)/u,
        'ptr_pre_of_ptr_exits':c.get('ptr_pre',0)/max(1,ptr_total),
        'force_left_changed':c.get('force_left_changed',0)/u,
        'force_right_changed':c.get('force_right_changed',0)/u,
        'pi_fast_all':c.get('pi_fast_all',0)/pi,
        'pi_domain_ptr_same':c.get('pi_domain_ptr_same',0)/pi,
        'pi_domain_ptr_nonfast':c.get('pi_domain_ptr_nonfast',0)/pi,
        'pi_domain_unify_true':c.get('pi_domain_unify_true',0)/pi,
        'pi_domain_unify_false':c.get('pi_domain_unify_false',0)/pi,
        'pi_body_unify_true':c.get('pi_body_unify_true',0)/pi,
        'pi_body_unify_false':c.get('pi_body_unify_false',0)/pi,
      }
    }
    rec['signals']={
      'PRE_FORCE_FASTPATH_HIGH': rec['shares']['ptr_pre_of_unify']>=0.10,
      'PRE_FORCE_DOMINATES_PTR_EXITS': rec['shares']['ptr_pre_of_ptr_exits']>=0.50,
      'PI_FASTPATH_HIGH': rec['shares']['pi_fast_all']>=0.25,
      'PI_REDUNDANT_DOMAIN_RECHECK_HIGH': rec['shares']['pi_domain_ptr_nonfast']>=0.10,
      'PI_BODY_WORK_DOMINANT': (c.get('pi_body_unify_true',0)+c.get('pi_body_unify_false',0))/pi>=0.50,
    }
    out.append(rec)

cross={
 'pre_force_fastpath_source_distinct':sum(r['signals']['PRE_FORCE_FASTPATH_HIGH'] for r in out)>=2,
 'pi_fastpath_source_distinct':sum(r['signals']['PI_FASTPATH_HIGH'] for r in out)>=2,
 'pi_redundant_domain_source_distinct':sum(r['signals']['PI_REDUNDANT_DOMAIN_RECHECK_HIGH'] for r in out)>=2,
}
report={'workloads':out,'cross_workload':cross}
(root/'preforce_pi_report.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report,indent=2))
