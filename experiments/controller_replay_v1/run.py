from dataclasses import dataclass

@dataclass(frozen=True)
class Snapshot:
    name: str
    residual: str
    repeated_local_failures: int
    residual_sharp: bool
    existing_structure_unknown: bool
    conditional_regimes: bool
    competing_explanations: int
    frozen_test_ready: bool
    expected: str

# Snapshots use only evidence available BEFORE the next historical move.
CASES = [
    Snapshot('pre_E0018','R3',2,True,False,False,2,True,'DISCRIMINATE'),
    Snapshot('pre_cache_class_map','R5',3,False,False,True,1,False,'MAP'),
    Snapshot('pre_canonical_env_audit','R6?',2,True,True,True,2,False,'INSPECT_CLOSURE'),
    Snapshot('pre_E0031','R8/R3',2,False,False,True,3,False,'MAP'),
    Snapshot('pre_E0034','R8/R3',3,True,False,False,2,True,'DISCRIMINATE'),
]

def controller(s):
    if s.existing_structure_unknown:
        return 'INSPECT_CLOSURE'
    if not s.residual_sharp:
        return 'MAP'
    if s.competing_explanations >= 2 and s.frozen_test_ready:
        return 'DISCRIMINATE'
    if s.repeated_local_failures >= 2 or s.conditional_regimes:
        return 'REFRAME'
    return 'EXPLOIT'

def local_only(s):
    # Strong local baseline: keep searching/testing within the current frame.
    return 'DISCRIMINATE' if s.frozen_test_ready else 'EXPLOIT'

def main():
    rows=[]
    for s in CASES:
        c=controller(s); b=local_only(s)
        rows.append((s.name,s.expected,c,b,c==s.expected,b==s.expected))
    cacc=sum(r[4] for r in rows)/len(rows)
    bacc=sum(r[5] for r in rows)/len(rows)
    print('case,expected,controller,local_only,controller_ok,local_ok')
    for r in rows: print(','.join(map(str,r)))
    print(f'controller_accuracy={cacc:.3f}')
    print(f'local_only_accuracy={bacc:.3f}')
    assert cacc > bacc
    assert cacc == 1.0

if __name__ == '__main__': main()
