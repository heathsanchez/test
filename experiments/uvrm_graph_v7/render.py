import json
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parent
DATA=json.loads((ROOT/'uvrm_graph_v5'/'cases.json').read_text())
UVRM='''Follow the verified residual process. Push the strongest current route; read the result as evidence; distinguish search, capability, representation/access, constructor, infrastructure, boundary and displacement failures; map when the residual is unclear; inspect closure before invention; state rivals; choose the smallest deciding test. Return MODE and NEXT MOVE. Do not use knowledge of later outcomes.'''
MASKS={'MASK_00':(), 'MASK_10':(0,), 'MASK_01':(1,), 'MASK_11':(0,1)}

def render(case, arm):
    ev='\n'.join(f'- {x}' for x in case['evidence'])
    idxs=MASKS[arm]
    body=f"Evidence nodes:\n{ev}"
    if idxs:
        rel='\n'.join(f'- {case["relations"][i][0]} -[{case["relations"][i][1]}]-> {case["relations"][i][2]}' for i in idxs)
        body += f"\n\nRetained typed scientific relations:\n{rel}"
    else:
        body += "\n\nRetained typed scientific relations: none"
    return f"{UVRM}\n\nDOMAIN: {case['domain']}\n\n{body}\n\nAnswer in two lines:\nMODE: <mode>\nNEXT MOVE: <specific experiment>"

def main():
    out=HERE/'rendered'; out.mkdir(exist_ok=True)
    for c in DATA['cases']:
        assert len(c['relations'])==2
        for arm in MASKS:
            (out/f"{c['id']}__{arm}.txt").write_text(render(c,arm)+'\n')
    print(f"rendered={len(DATA['cases'])*len(MASKS)}")
if __name__=='__main__': main()
