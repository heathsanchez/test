import ast, os, json
from pathlib import Path
import river_client as river

BASE='Qwen/Qwen3.5-9B'; SEED=20260831
STABLE='river://ae6fa294-181b-46af-b078-429ce7e6c882/weights/quix_AB_step1'
REGRESSED='river://8c23d218-606e-4b90-a4df-d8a9c86ef554/weights/v160_first_regression_step5'
OUT=Path('artifacts/v161_ast_role_experiential_rescue'); OUT.mkdir(parents=True,exist_ok=True)
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()

TESTS={
 'A':[([[]],[]),([[30]],[30]),([[10,'-',5,'-',2]],[10,5,'-',2,'-']),([[34,'-',12,'/',5]],[34,12,5,'/','-']),([[4,'+',9,'*',9,'-',10,'+',13]],[4,9,9,'*','+',10,'-',13,'+'])],
 'B':[([1],[]),([100],[2,2,5,5]),([101],[101]),([104],[2,2,2,13]),([2],[2]),([63],[3,3,7]),([9837],[3,3,1093])],
}
A_EXPERIENCE=[
 {'arg':'stream','prec':'priority','out':'result','stack':'operators','item':'symbol'},
 {'arg':'sequence','prec':'ranking','out':'postfix','stack':'holding','item':'entry'},
]
B_EXPERIENCE=[
 {'n':'candidate','i':'factor'},
 {'n':'value','i':'trial'},
]
A_HELD=[
 {'arg':'lexemes','prec':'binding','out':'answer','stack':'pending','item':'lexeme'},
 {'arg':'parts','prec':'strength','out':'emitted','stack':'ops','item':'part'},
 {'arg':'input_tokens','prec':'order','out':'queue','stack':'work','item':'tok'},
 {'arg':'pieces','prec':'power','out':'output','stack':'waiting','item':'piece'},
 {'arg':'terms','prec':'level','out':'rpn','stack':'shelf','item':'term'},
 {'arg':'items','prec':'weight','out':'built','stack':'buffer','item':'current'},
 {'arg':'symbols','prec':'rank','out':'converted','stack':'hold','item':'sym'},
 {'arg':'elements','prec':'precedence','out':'final','stack':'operator_bin','item':'element'},
]
B_HELD=[
 {'n':'integer','i':'probe'}, {'n':'amount','i':'divisor'}, {'n':'target_num','i':'candidate_div'}, {'n':'whole','i':'test_factor'},
 {'n':'input_value','i':'possible'}, {'n':'number','i':'d'}, {'n':'remaining','i':'p'}, {'n':'quantity','i':'f'},
]

def spec(task,names):
 if task=='A':
  a,p,o,s,it=[names[k] for k in ['arg','prec','out','stack','item']]
  src=f'''def target({a}):\n    {p}={{'+':1,'-':1,'*':2,'/':2}}\n    {o}=[]\n    {s}=[]\n    for {it} in {a}:\n        if isinstance({it}, int):\n            {o}.append({it})\n        else:\n            while {s} and {p}[{it}] <= {p}[{s}[-1]]:\n                {o}.append({s}.pop())\n            # PATCH_HERE\n    while {s}:\n        {o}.append({s}.pop())\n    return {o}\n'''
  ans=f'{s}.append({it})'
 else:
  n,i=names['n'],names['i']
  src=f'''def target({n}):\n    if {n} == 1:\n        return []\n    for {i} in range(2, int({n} ** 0.5) + 1):\n        if {n} % {i} == 0:\n            return [{i}] + target({n} // {i})\n    # PATCH_HERE\n'''
  ans=f'return [{n}]'
 return src,ans

def prompt(task,names,mem=None):
 src,_=spec(task,names); examples='; '.join(f'{x[0]} -> {x[1]}' for x in TESTS[task][:3])
 memory='' if not mem else '\nVerified prior experience:\n'+'\n'.join(mem)+'\n'
 return f'''Repair this Python function. Replace # PATCH_HERE with exactly one Python line.\nFailing/expected examples: {examples}.{memory}\n{src}\nReturn ONLY the replacement line.'''

def clean(text):
 t=text.strip().splitlines()[0].strip() if text.strip() else ''
 t=t.strip('`').strip()
 if t.startswith('python '): t=t[7:].strip()
 return t

def verify(task,names,line):
 src,_=spec(task,names)
 marker='            # PATCH_HERE' if task=='A' else '    # PATCH_HERE'; indent='            ' if task=='A' else '    '
 ns={}
 try:
  patched=src.replace(marker,indent+line); exec(compile(patched,'<candidate>','exec'),ns,ns)
 except Exception: return False
 fn=ns['target']
 for args,exp in TESTS[task]:
  try: got=fn(*args)
  except Exception: return False
  if got!=exp:return False
 return True

def sample(m,task,cases,mem=None):
 ps=[prompt(task,n,mem) for n in cases]; gs=m.sample(prompts=ps,max_tokens=28,temperature=0.0)
 return [clean(g[0].text) for g in gs]

def source_roles_A(src):
 tree=ast.parse(src); fn=tree.body[0]
 loop_target=None; empty=[]; while_names=set()
 for node in ast.walk(fn):
  if isinstance(node,ast.For) and isinstance(node.target,ast.Name): loop_target=node.target.id
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and isinstance(node.value,ast.List) and not node.value.elts:
   empty.append(node.targets[0].id)
  if isinstance(node,ast.While):
   while_names |= {x.id for x in ast.walk(node.test) if isinstance(x,ast.Name)}
 stack_candidates=[x for x in empty if x in while_names]
 if loop_target is None or len(stack_candidates)!=1:return None
 return {'STACK':stack_candidates[0],'LOOP_ITEM':loop_target}

def source_roles_B(src):
 tree=ast.parse(src); fn=tree.body[0]
 if not fn.args.args:return None
 return {'FUNC_ARG':fn.args.args[0].arg}

def induce_descriptor(task,src,line):
 try: node=ast.parse(line).body[0]
 except Exception:return None
 if task=='A':
  roles=source_roles_A(src)
  if not roles or not isinstance(node,ast.Expr) or not isinstance(node.value,ast.Call):return None
  call=node.value
  if not isinstance(call.func,ast.Attribute) or call.func.attr!='append' or not isinstance(call.func.value,ast.Name):return None
  if len(call.args)!=1 or not isinstance(call.args[0],ast.Name):return None
  if call.func.value.id==roles['STACK'] and call.args[0].id==roles['LOOP_ITEM']:
   return 'A_APPEND_STACK_LOOP_ITEM'
 else:
  roles=source_roles_B(src)
  if not roles or not isinstance(node,ast.Return) or not isinstance(node.value,ast.List) or len(node.value.elts)!=1:return None
  x=node.value.elts[0]
  if isinstance(x,ast.Name) and x.id==roles['FUNC_ARG']:return 'B_RETURN_SINGLETON_ARG'
 return None

def instantiate(desc,task,names):
 src,_=spec(task,names)
 if desc=='A_APPEND_STACK_LOOP_ITEM':
  r=source_roles_A(src); return None if not r else f"{r['STACK']}.append({r['LOOP_ITEM']})"
 if desc=='B_RETURN_SINGLETON_ARG':
  r=source_roles_B(src); return None if not r else f"return [{r['FUNC_ARG']}]"
 return ''

def eval_model(m,task,cases,mem=None):
 lines=sample(m,task,cases,mem); return {'hits':sum(verify(task,n,l) for n,l in zip(cases,lines)),'n':len(cases),'lines':lines}

R={'protocol':'V161 frozen AST-role experiential rescue','experience':{},'maps':{},'arms':{}}
# Learn only from stable model outputs that pass executable verification.
with client.session(project='v161-experience') as s:
 m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=STABLE)
 for task,cases in [('A',A_EXPERIENCE),('B',B_EXPERIENCE)]:
  lines=sample(m,task,cases); episodes=[]; descs=[]
  for names,line in zip(cases,lines):
   src,_=spec(task,names); ok=verify(task,names,line); d=induce_descriptor(task,src,line) if ok else None
   episodes.append({'names':names,'line':line,'verified':ok,'descriptor':d}); descs.append(d)
  learned=descs[0] if len(set(descs))==1 and descs[0] is not None else None
  R['experience'][task]=episodes; R['maps'][task]=learned
if any(R['maps'].get(t) is None for t in ['A','B']):
 R['verdict']='EXPERIENCE_MAP_NOT_LEARNED'; json.dump(R,open(OUT/'RESULT.json','w'),indent=2); print(json.dumps(R,indent=2)); raise SystemExit

# Raw-memory text is frozen from admitted prior episodes.
mem={}
for task in ['A','B']:
 mem[task]=[f"Source identifiers {e['names']} => verified repair: {e['line']}" for e in R['experience'][task] if e['verified']]

with client.session(project='v161-frozen-regressed') as s:
 m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=REGRESSED)
 neural={}; raw={}
 for task,cases in [('A',A_HELD),('B',B_HELD)]:
  neural[task]=eval_model(m,task,cases)
  raw[task]=eval_model(m,task,cases,mem[task])
R['arms']['neural_only']=neural; R['arms']['raw_verified_memory']=raw

compiled={}; shuffled={}; wrong={'A':R['maps']['B'],'B':R['maps']['A']}
for task,cases in [('A',A_HELD),('B',B_HELD)]:
 lines=[instantiate(R['maps'][task],task,n) for n in cases]
 compiled[task]={'hits':sum(verify(task,n,l) for n,l in zip(cases,lines)),'n':len(cases),'lines':lines}
 wlines=[instantiate(wrong[task],task,n) for n in cases]
 shuffled[task]={'hits':sum(verify(task,n,l) for n,l in zip(cases,wlines)),'n':len(cases),'lines':wlines}
R['arms']['compiled_experiential_map']=compiled; R['arms']['shuffled_map']=shuffled

tot={arm:sum(R['arms'][arm][t]['hits'] for t in ['A','B']) for arm in R['arms']}
R['totals']=tot
R['verdict']='PASS_AST_ROLE_EXPERIENTIAL_RESCUE' if tot['compiled_experiential_map']>max(tot['neural_only'],tot['raw_verified_memory']) and tot['compiled_experiential_map']>tot['shuffled_map'] else 'NO_DECISIVE_AST_ROLE_RESCUE'
json.dump(R,open(OUT/'RESULT.json','w'),indent=2); print(json.dumps(R,indent=2),flush=True)
