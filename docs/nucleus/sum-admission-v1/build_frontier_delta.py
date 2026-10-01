"""Render the observed dependency-boundary change; never infer whole-file gains."""
import json
import pathlib
import re
import sys

before=json.loads(pathlib.Path(sys.argv[1]).read_text())
after=json.loads(pathlib.Path(sys.argv[2]).read_text())
old={r['test']:r for r in before}
def boundary(row):
    lines=re.findall(r'^NUCLEUS_DOWNSTREAM:.*$',row['trace'],re.M)
    return lines[-1] if lines else None
rows=[{'test':r['test'],'expected':r['expected'],
       'before':old[r['test']]['candidate'],'after':r['candidate'],
       'before_boundary':boundary(old[r['test']]),'after_boundary':boundary(r)} for r in after]
result={'boundary':'194 pinned downloadable tests; former 24 UNKNOWNs',
        'whole_file_gains':[r['test'] for r in rows if r['before']==2 and r['after']==r['expected']],
        'advanced_boundaries':[r for r in rows if r['before_boundary']!=r['after_boundary']],
        'rows':rows}
pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
