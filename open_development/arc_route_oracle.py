"""Independent exhaustive route evaluator for the frozen ARC micro-language."""
from collections import Counter
from .arc_discrimination import D4, NEW

def G(x):return tuple(tuple(int(v) for v in r) for r in x)
def R(g):return tuple(zip(*g[::-1]))
def T(g,n):
 g=G(g);a=R(g);b=R(a);c=R(b)
 return {"id":g,"r90":a,"r180":b,"r270":c,"flip-h":tuple(tuple(reversed(r)) for r in g),"flip-v":tuple(reversed(g)),"transpose":tuple(zip(*g)),"anti":tuple(zip(*tuple(reversed(g))))[::-1]}[n]
def C(g):
 g=G(g);q=[(i,j)for i,r in enumerate(g)for j,v in enumerate(r)if v]
 if not q:return g
 a,b=min(i for i,j in q),max(i for i,j in q);c,d=min(j for i,j in q),max(j for i,j in q)
 return tuple(r[c:d+1]for r in g[a:b+1])
def F(g,z):
 k,n=z.split(":",1);g=G(g);h=T(g,n)
 if k=="concat-h" and len(g)==len(h):return tuple(a+b for a,b in zip(g,h))
 if k=="concat-v" and len(g[0])==len(h[0]):return g+h
 if k=="overlay" and (len(g),len(g[0]))==(len(h),len(h[0])):return tuple(tuple(max(x,y)for x,y in zip(a,b))for a,b in zip(g,h))
def ok(task,fn):
 try:return all(fn(G(e["input"]))==G(e["output"])for e in tuple(task["train"])+tuple(task["test"]))
 except Exception:return False
def execute(state,rid,g,active=()):
 if rid in active:return None
 rec=state["capabilities"].get(rid)
 if not rec:return None
 body=rec["repair"]["payload"].get("body",{});op=body.get("op")
 if op=="d4":return T(g,body["name"])
 parent=body.get("callee")
 if rec["repair"]["dependencies"]!=[parent]:return None
 if op=="crop-call":return execute(state,parent,C(g),(*active,rid))
 if op=="extend":
  h=execute(state,parent,g,(*active,rid));k=body["spec"].split(":",1)[0]
  if h is None:return None
  if k=="concat-h" and len(g)==len(h):return tuple(a+b for a,b in zip(G(g),h))
  if k=="concat-v" and len(g[0])==len(h[0]):return G(g)+h
  if k=="overlay" and (len(g),len(g[0]))==(len(h),len(h[0])):return tuple(tuple(max(x,y)for x,y in zip(a,b))for a,b in zip(G(g),h))
def route(task,state):
 if any(ok(task,lambda g,r=r:execute(state,r,g))for r in state["capabilities"]):return "REUSE"
 if any(ok(task,lambda g,n=n:T(C(g),n))for n in D4):return "EXAPTATION"
 if any(ok(task,lambda g,z=z:F(g,z))for z in NEW):return "EXPANSION"
 return "UNKNOWN"
