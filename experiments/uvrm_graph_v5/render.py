import json
from pathlib import Path
HERE=Path(__file__).parent
DATA=json.loads((HERE/'cases.json').read_text())
UVRM='''Follow the verified residual process. Push the strongest current route; read the result as evidence; distinguish search, capability, representation/access, constructor, infrastructure, boundary and displacement failures; map when the residual is unclear; inspect closure before invention; state rivals; choose the smallest deciding test. Return MODE and NEXT MOVE. Do not use knowledge of later outcomes.'''

def render(case, arm):
    ev='\n'.join(f'- {x}' for x in case['evidence'])
    if arm=='TRANSCRIPT':
        body=f"Chronological research notes:\n{ev}"
    elif arm=='GRAPH_ABL':
        rel='\n'.join(f'- {a} -> {b}' for a,_,b in case['relations'])
        body=f"Evidence nodes:\n{ev}\n\nRelated objects (edge labels withheld):\n{rel}"
    elif arm in ('GRAPH','GRAPH_RULES'):
        rel='\n'.join(f'- {a} -[{t}]-> {b}' for a,t,b in case['relations'])
        body=f"Evidence nodes:\n{ev}\n\nTyped scientific relations:\n{rel}"
        if arm=='GRAPH_RULES':
            body += '\n\nController scaffold: MAP when mechanism is not localized; DISCRIMINATE when rival mechanisms need a matched separator; VERIFY when a candidate needs protected causal confirmation; TRANSFER when later generalization is unresolved; REFRAME only after a bounded family/representation is genuinely exhausted.'
    else: raise ValueError(arm)
    return f"{UVRM}\n\nDOMAIN: {case['domain']}\n\n{body}\n\nAnswer in two lines:\nMODE: <mode>\nNEXT MOVE: <specific experiment>"

def main():
    out=HERE/'rendered'; out.mkdir(exist_ok=True)
    for c in DATA['cases']:
        for arm in ('TRANSCRIPT','GRAPH_ABL','GRAPH','GRAPH_RULES'):
            (out/f"{c['id']}__{arm}.txt").write_text(render(c,arm)+'\n')
    print(f"rendered={len(DATA['cases'])*4}")
if __name__=='__main__': main()
