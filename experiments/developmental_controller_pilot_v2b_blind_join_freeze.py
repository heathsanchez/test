#!/usr/bin/env python3
"""Phase-1 freeze for Developmental Controller Pilot v2b.

This file intentionally contains only heterogeneous residual packets and the
semantic JOIN outputs frozen *before* the downstream target/candidate set is
revealed.  Hidden signatures and evaluation are added in a later commit.

Axes used by the frozen JOIN are semantic properties, not source vocabulary:
  I = current identity/quotient is too coarse
  S = applicability/scope is overbroad
  C = successful repair requires cross-component composition
  K = discovering/representing the reusable object dominates application cost

The semantic JOIN must infer one four-bit K vector from all three source
channels.  No downstream database candidates or answer labels are present here.
"""

EVIDENCE = [
{"id":0,"evidence":[{"channel":"sair","statement":"The current quotient identifies implication cases that finite models separate, although the repaired constructor transfers across neighboring source families."},{"channel":"code","statement":"The repair rule applies across the contexts it is offered, and each failing site can be corrected independently."},{"channel":"kernel","statement":"Pointer-identical states later diverge under checking, and finding a semantic key fine enough to separate them costs nearly as much as materializing the result."}]},
{"id":1,"evidence":[{"channel":"kernel","statement":"Objects sharing the runtime key later normalize differently, although adding the missing discriminator is cheap."},{"channel":"code","statement":"The repair is valid across its activation region, but the failing behavior disappears only when two separated AST roles are changed together."},{"channel":"sair","statement":"The current quotient identifies implication cases that finite models separate, although the repaired constructor transfers across neighboring source families."}]},
{"id":2,"evidence":[{"channel":"sair","statement":"The quotient is extensionally sound, but a constructor learned in one source family fails on a neighboring family admitted by the same trigger."},{"channel":"kernel","statement":"Cache classes stay semantically uniform, and finding a reusable key is cheap relative to execution."},{"channel":"code","statement":"The learned trigger includes contexts where the edit is wrong, and the genuine repair also requires coordinated changes at two separated AST roles."}]},
{"id":3,"evidence":[{"channel":"code","statement":"The edit itself is local, but a trigger learned from one context fires in another context where the same transform breaks behavior."},{"channel":"kernel","statement":"Objects sharing the runtime key later normalize differently, although adding the missing discriminator is cheap."},{"channel":"sair","statement":"A source class treated as one quotient contains verifier-distinct cases, and the constructor also fails outside a narrower residual basin."}]},
{"id":4,"evidence":[{"channel":"kernel","statement":"Cache classes stay semantically faithful, but constructing the canonical representative costs about as much as the computation it should reuse."},{"channel":"sair","statement":"The quotient is extensionally sound, but a constructor learned in one source family fails on a neighboring family admitted by the same trigger."},{"channel":"code","statement":"The edit itself is local, but a trigger learned from one context fires in another context where the same transform breaks behavior."}]},
{"id":5,"evidence":[{"channel":"kernel","statement":"Pointer-identical states later diverge under checking, and finding a semantic key fine enough to separate them costs nearly as much as materializing the result."},{"channel":"code","statement":"The edit itself is local, but a trigger learned from one context fires in another context where the same transform breaks behavior."},{"channel":"sair","statement":"A source class treated as one quotient contains verifier-distinct cases, and the constructor also fails outside a narrower residual basin."}]},
{"id":6,"evidence":[{"channel":"code","statement":"The learned trigger includes contexts where the edit is wrong, and the genuine repair also requires coordinated changes at two separated AST roles."},{"channel":"sair","statement":"A source class treated as one quotient contains verifier-distinct cases, and the constructor also fails outside a narrower residual basin."},{"channel":"kernel","statement":"Pointer-identical states later diverge under checking, and finding a semantic key fine enough to separate them costs nearly as much as materializing the result."}]},
{"id":7,"evidence":[{"channel":"kernel","statement":"Cache classes stay semantically faithful, but constructing the canonical representative costs about as much as the computation it should reuse."},{"channel":"code","statement":"The learned trigger includes contexts where the edit is wrong, and the genuine repair also requires coordinated changes at two separated AST roles."},{"channel":"sair","statement":"The quotient is extensionally sound, but a constructor learned in one source family fails on a neighboring family admitted by the same trigger."}]},
{"id":8,"evidence":[{"channel":"kernel","statement":"Objects sharing the runtime key later normalize differently, although adding the missing discriminator is cheap."},{"channel":"code","statement":"The repair rule applies across the contexts it is offered, and each failing site can be corrected independently."},{"channel":"sair","statement":"The current quotient identifies implication cases that finite models separate, although the repaired constructor transfers across neighboring source families."}]},
{"id":9,"evidence":[{"channel":"sair","statement":"The quotient is extensionally sound, but a constructor learned in one source family fails on a neighboring family admitted by the same trigger."},{"channel":"kernel","statement":"Cache classes stay semantically uniform, and finding a reusable key is cheap relative to execution."},{"channel":"code","statement":"The edit itself is local, but a trigger learned from one context fires in another context where the same transform breaks behavior."}]},
{"id":10,"evidence":[{"channel":"kernel","statement":"Cache classes stay semantically uniform, and finding a reusable key is cheap relative to execution."},{"channel":"code","statement":"The repair rule applies across the contexts it is offered, and each failing site can be corrected independently."},{"channel":"sair","statement":"The quotient classes remain extensionally uniform, and the learned constructor transfers across neighboring source families."}]},
{"id":11,"evidence":[{"channel":"sair","statement":"The quotient classes remain extensionally uniform, and the learned constructor transfers across neighboring source families."},{"channel":"code","statement":"The repair rule applies across the contexts it is offered, and each failing site can be corrected independently."},{"channel":"kernel","statement":"Cache classes stay semantically faithful, but constructing the canonical representative costs about as much as the computation it should reuse."}]},
{"id":12,"evidence":[{"channel":"code","statement":"The repair is valid across its activation region, but the failing behavior disappears only when two separated AST roles are changed together."},{"channel":"sair","statement":"The quotient classes remain extensionally uniform, and the learned constructor transfers across neighboring source families."},{"channel":"kernel","statement":"Cache classes stay semantically faithful, but constructing the canonical representative costs about as much as the computation it should reuse."}]},
{"id":13,"evidence":[{"channel":"sair","statement":"The quotient classes remain extensionally uniform, and the learned constructor transfers across neighboring source families."},{"channel":"kernel","statement":"Cache classes stay semantically uniform, and finding a reusable key is cheap relative to execution."},{"channel":"code","statement":"The repair is valid across its activation region, but the failing behavior disappears only when two separated AST roles are changed together."}]},
{"id":14,"evidence":[{"channel":"code","statement":"The learned trigger includes contexts where the edit is wrong, and the genuine repair also requires coordinated changes at two separated AST roles."},{"channel":"kernel","statement":"Objects sharing the runtime key later normalize differently, although adding the missing discriminator is cheap."},{"channel":"sair","statement":"A source class treated as one quotient contains verifier-distinct cases, and the constructor also fails outside a narrower residual basin."}]},
{"id":15,"evidence":[{"channel":"code","statement":"The repair is valid across its activation region, but the failing behavior disappears only when two separated AST roles are changed together."},{"channel":"sair","statement":"The current quotient identifies implication cases that finite models separate, although the repaired constructor transfers across neighboring source families."},{"channel":"kernel","statement":"Pointer-identical states later diverge under checking, and finding a semantic key fine enough to separate them costs nearly as much as materializing the result."}]}
]

# Frozen semantic JOIN outputs, produced from EVIDENCE only, before target reveal.
# Order is (I,S,C,K).
FROZEN_JOIN_K = {
0:(1,0,0,1), 1:(1,0,1,0), 2:(0,1,1,0), 3:(1,1,0,0),
4:(0,1,0,1), 5:(1,1,0,1), 6:(1,1,1,1), 7:(0,1,1,1),
8:(1,0,0,0), 9:(0,1,0,0), 10:(0,0,0,0), 11:(0,0,0,1),
12:(0,0,1,1), 13:(0,0,1,0), 14:(1,1,1,0), 15:(1,0,1,1),
}

FROZEN_JOIN_EXPLANATION = {
"I":"whether the current identity/quotient collapses states reality distinguishes",
"S":"whether the capability is activated outside the regime where it is valid",
"C":"whether the required change is irreducibly coordinated across components",
"K":"whether identifying/representing the reusable object costs about as much as applying it",
}
