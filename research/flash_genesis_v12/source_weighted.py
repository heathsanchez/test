"""SOURCE-only V12 weighted examples: V11's opened future objectives, now source.
Also adds a weighted uniform-matroid development control.
"""
from dataclasses import dataclass
import sys
from pathlib import Path
parent=Path(__file__).resolve().parents[1]/'flash_genesis_v11'
sys.path.insert(0,str(parent))
from protected_oracles import frozen_changed_objectives
@dataclass(frozen=True)
class S:
    name:str
    n:int
    feasible:object
    weights:tuple
    score:object

def additive(m,weights):return sum(weights[i] for i in range(len(weights)) if m>>i&1)

def families():
    prior=[S(name,n,independent,tuple(weights),lambda m,w=tuple(weights):additive(m,w))
          for name,n,independent,weights in frozen_changed_objectives()]
    weights=(1,7,2,14,4,9)
    prior.append(S('source_weighted_uniform',6,lambda m:m.bit_count()<=2,
                   weights,lambda m,w=weights:additive(m,w)))
    return prior
