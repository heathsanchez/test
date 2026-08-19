#!/usr/bin/env python3
from pathlib import Path
import subprocess
subprocess.run(['python3','scripts/generate_developmental_distinction_invention_v19.py'],check=True)
src=Path('scripts/run_developmental_distinction_invention_v19.py')
dst=Path('scripts/run_developmental_distinction_invention_v20.py')
s=src.read_text()
s=s.replace('developmental-distinction-invention-v19','developmental-distinction-invention-v20')
s=s.replace('fault-v19-','fault-v20-')
s=s.replace("FEATURES=['last_depth_bucket','depth_span_bucket','terminal_depth_role','terminal_depth_repeat','depth_turn_bucket','depth_distinct_bucket','first_last_depth_relation']", "FEATURES=['last_depth_bucket','depth_distinct_bucket','terminal_visit_bucket','terminal_gap_bucket','revisit_ratio_bucket','head_delta_pattern','tail_delta_pattern','extremum_order','return_to_start']")
needle="""    else:\n        depth_span_bucket=terminal_depth_role=terminal_depth_repeat=depth_turn_bucket=depth_distinct_bucket=first_last_depth_relation='NONE'\n    return {\n"""
insert="""    else:\n        depth_span_bucket=terminal_depth_role=terminal_depth_repeat=depth_turn_bucket=depth_distinct_bucket=first_last_depth_relation='NONE'\n    if depths:\n        lastd=depths[-1]\n        visits=sum(1 for x in depths if x==lastd)\n        terminal_visit_bucket='1' if visits==1 else ('2_3' if visits<=3 else 'ge4')\n        prev=[i for i,x in enumerate(depths[:-1]) if x==lastd]\n        gap=(len(depths)-1-prev[-1]) if prev else 999999\n        terminal_gap_bucket='new' if not prev else ('1_2' if gap<=2 else ('3_7' if gap<=7 else 'ge8'))\n        revisits=len(depths)-len(set(depths))\n        rr=revisits/max(1,len(depths))\n        revisit_ratio_bucket='low' if rr<0.25 else ('mid' if rr<0.6 else 'high')\n        def pat(seq):\n            signs=[]\n            for a,b in zip(seq,seq[1:]):\n                signs.append('U' if b>a else ('D' if b<a else 'F'))\n            return ''.join(signs) or 'NONE'\n        head_delta_pattern=pat(depths[:5])\n        tail_delta_pattern=pat(depths[-5:])\n        imin=depths.index(min(depths)); imax=depths.index(max(depths))\n        extremum_order='min_first' if imin<imax else ('max_first' if imax<imin else 'same')\n        return_to_start='yes' if len(depths)>1 and depths[-1]==depths[0] else 'no'\n    else:\n        terminal_visit_bucket=terminal_gap_bucket=revisit_ratio_bucket=head_delta_pattern=tail_delta_pattern=extremum_order=return_to_start='NONE'\n    return {\n"""
if needle not in s: raise SystemExit('V20 relational motif anchor missing')
s=s.replace(needle,insert,1)
needle2="""      'first_last_depth_relation': first_last_depth_relation,\n"""
add2="""      'first_last_depth_relation': first_last_depth_relation,\n      'terminal_visit_bucket':terminal_visit_bucket,\n      'terminal_gap_bucket':terminal_gap_bucket,\n      'revisit_ratio_bucket':revisit_ratio_bucket,\n      'head_delta_pattern':head_delta_pattern,\n      'tail_delta_pattern':tail_delta_pattern,\n      'extremum_order':extremum_order,\n      'return_to_start':return_to_start,\n"""
if needle2 not in s: raise SystemExit('V20 feature dictionary anchor missing')
s=s.replace(needle2,add2,1)
s=s.replace("'status':'LIVE_RELATIONAL_DISTINCTION_INVENTION_V19'", "'status':'LIVE_RELATIONAL_TRANSITION_INVENTION_V20'")
s=s.replace("'invented_relational_family':['depth_span_bucket','terminal_depth_role','terminal_depth_repeat','depth_turn_bucket','depth_distinct_bucket','first_last_depth_relation']", "'invented_relational_family':['terminal_visit_bucket','terminal_gap_bucket','revisit_ratio_bucket','head_delta_pattern','tail_delta_pattern','extremum_order','return_to_start']")
s=s.replace("if train_error!=0: raise SystemExit('invented relational vocabulary did not close V18 obstruction')", "if train_error!=0: raise SystemExit('transition-motif invention did not close V19 residual')")
s=s.replace("if hold_acc!=1.0: raise SystemExit('invented relational quotient failed source-distinct transfer')", "if hold_acc!=1.0: raise SystemExit('transition-motif quotient failed source-distinct transfer')")
dst.write_text(s)
print('generated V20 relational transition motifs for V19 residual')
