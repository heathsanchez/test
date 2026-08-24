import json
from pathlib import Path
HERE=Path(__file__).parent
V5=HERE.parent/'uvrm_graph_v5'
DATA=json.loads((V5/'cases.json').read_text())
UVRM='''Follow the verified residual process. Push the strongest current route; read the result as evidence; distinguish search, capability, representation/access, constructor, infrastructure, boundary and displacement failures; map when the residual is unclear; inspect closure before invention; state rivals; choose the smallest deciding test. Return MODE and NEXT MOVE. Do not use knowledge of later outcomes.'''
WRONG={'SUPPORTS':'REFUTES','REFUTES':'SUPPORTS','MOTIVATES':'WEAKENS','WEAKENS':'MOTIVATES','BLOCKS':'SUPPORTS'}

def evidence(case): return '\n'.join(f'- {x}' for x in case['evidence'])
def typed(case,permuted=False):
    rows=[]
    for a,t,b in case['relations']:
        if permuted: t=WRONG.get(t,'REFUTES')
        rows.append(f'- {a} -[{t}]-> {b}')
    return '\n'.join(rows)

def final_prompt(case,arm,reconstruction=None):
    ev=evidence(case)
    if arm=='RAW': body=f"Chronological research notes:\n{ev}"
    elif arm=='RECONSTRUCT_1':
        body=f"Chronological research notes:\n{ev}\n\nBefore selecting the next move, internally reconstruct the smallest decision-relevant relations among these observations. Do not assume supplied relation labels or later outcomes."
    elif arm=='RECONSTRUCT_2':
        body=f"Chronological research notes:\n{ev}\n\nA separate reconstruction pass, derived only from those same notes, produced:\n{reconstruction}\n\nUse it only if supported by the raw evidence; then choose the next deciding move."
    elif arm=='GRAPH': body=f"Evidence nodes:\n{ev}\n\nTyped scientific relations:\n{typed(case)}"
    elif arm=='GRAPH_PERMUTED': body=f"Evidence nodes:\n{ev}\n\nTyped scientific relations:\n{typed(case,True)}"
    else: raise ValueError(arm)
    return f"{UVRM}\n\nDOMAIN: {case['domain']}\n\n{body}\n\nAnswer in two lines:\nMODE: <mode>\nNEXT MOVE: <specific experiment>"

def reconstruction_prompt(case):
    return f'''You are a scientific-state reconstruction pass. From ONLY the chronological evidence below, infer a compact relation graph that would help another agent choose the next experiment. Do not choose the next experiment and do not use later outcomes. Emit at most four lines of the form A -[RELATION]-> B. Use relation names only when justified by the evidence.\n\nDOMAIN: {case['domain']}\nChronological evidence:\n{evidence(case)}'''
