#!/usr/bin/env python3
from pathlib import Path
import subprocess
subprocess.run(['python3','scripts/generate_developmental_distinction_invention_v20.py'],check=True)
src=Path('scripts/run_developmental_distinction_invention_v20.py')
dst=Path('scripts/run_developmental_distinction_quotient_v21.py')
s=src.read_text()
s=s.replace('developmental-distinction-invention-v20','developmental-distinction-quotient-v21')
s=s.replace('fault-v20-','fault-v21-')
s=s.replace('DEV_PER_FAMILY=2','DEV_PER_FAMILY=3')
s=s.replace("FEATURES=['last_depth_bucket','depth_distinct_bucket','terminal_visit_bucket','terminal_gap_bucket','revisit_ratio_bucket','head_delta_pattern','tail_delta_pattern','extremum_order','return_to_start']", "FEATURES=['final_depth_step']")
needle="""        return_to_start='yes' if len(depths)>1 and depths[-1]==depths[0] else 'no'\n    else:\n        terminal_visit_bucket=terminal_gap_bucket=revisit_ratio_bucket=head_delta_pattern=tail_delta_pattern=extremum_order=return_to_start='NONE'\n    return {\n"""
insert="""        return_to_start='yes' if len(depths)>1 and depths[-1]==depths[0] else 'no'\n        if len(depths)<2: final_depth_step='NONE'\n        elif depths[-1]>depths[-2]: final_depth_step='U'\n        elif depths[-1]<depths[-2]: final_depth_step='D'\n        else: final_depth_step='F'\n    else:\n        terminal_visit_bucket=terminal_gap_bucket=revisit_ratio_bucket=head_delta_pattern=tail_delta_pattern=extremum_order=return_to_start='NONE'\n        final_depth_step='NONE'\n    return {\n"""
if needle not in s: raise SystemExit('V21 quotient anchor missing')
s=s.replace(needle,insert,1)
needle2="""      'return_to_start':return_to_start,\n"""
add2="""      'return_to_start':return_to_start,\n      'final_depth_step':final_depth_step,\n"""
if needle2 not in s: raise SystemExit('V21 feature dictionary anchor missing')
s=s.replace(needle2,add2,1)
s=s.replace("'status':'LIVE_RELATIONAL_TRANSITION_INVENTION_V20'", "'status':'LIVE_MINIMAL_RELATIONAL_QUOTIENT_V21'")
s=s.replace("'invented_relational_family':['terminal_visit_bucket','terminal_gap_bucket','revisit_ratio_bucket','head_delta_pattern','tail_delta_pattern','extremum_order','return_to_start']", "'quotiented_relational_family':['final_depth_step']")
s=s.replace("if train_error!=0: raise SystemExit('transition-motif invention did not close V19 residual')", "if train_error!=0: raise SystemExit('minimal final-step quotient insufficient on derivation set')")
s=s.replace("if hold_acc!=1.0: raise SystemExit('transition-motif quotient failed source-distinct transfer')", "if hold_acc!=1.0: raise SystemExit('minimal final-step quotient failed fresh source-distinct transfer')")
dst.write_text(s)
print('generated V21 minimal final-depth-step quotient with fresh fourth-case holdouts')
