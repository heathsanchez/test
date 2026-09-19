#!/usr/bin/env python3
"""Phase 1: Developmental Controller Pilot v3 -- unsupplied specification.

This phase contains ONLY heterogeneous residual fields and a frozen semantic
specification induced from them.  The benchmark does not provide axis names,
bit positions, target-domain candidates, or answer labels here.

Scientific boundary: the residual sentences are synthetic and author-designed.
The test is whether a semantic JOIN can invent a compact cross-domain coordinate
system and encode each field in it before downstream target reveal; it is not yet
an open-ended real-science claim.
"""

EVIDENCE = [
 {"id":0,"evidence":[
  {"channel":"compiler","statement":"Repeating the same optimization after an intervening pass gives a different result even though the visible IR at the decision point looks unchanged."},
  {"channel":"planner","statement":"Two plans with identical local observations diverge because one consumed a shared budget token earlier."},
  {"channel":"proof","statement":"The local goal and hypotheses are unchanged, but a previously used lemma can no longer be consumed in the same branch."}]},
 {"id":1,"evidence":[
  {"channel":"proof","statement":"Two proof states print identically although a hidden universe assignment makes only one continuation type-correct."},
  {"channel":"planner","statement":"The action can be repeated without depletion, and its effect does not depend on what happened before."},
  {"channel":"compiler","statement":"The pass is locally reversible, but two visually identical nodes carry different alias provenance and optimize differently."}]},
 {"id":2,"evidence":[
  {"channel":"planner","statement":"The same move has a different effect after an earlier commitment, while every currently visible feature is the same."},
  {"channel":"compiler","statement":"The transform is reversible and uses no shared scarce resource; the only discrepancy is dependence on transformation history."},
  {"channel":"proof","statement":"Replaying the same tactic after a prior normalization step changes the reachable continuation despite the same printed state."}]},
 {"id":3,"evidence":[
  {"channel":"compiler","statement":"Two nodes look identical but differ in hidden alias provenance; additionally the rewrite spends a one-use ownership permission."},
  {"channel":"proof","statement":"Printed states coincide while hidden metavariable assignments differ, and one branch consumes a linear hypothesis."},
  {"channel":"planner","statement":"Locally identical situations hide different reservations, and executing the move irreversibly spends the reservation."}]},
 {"id":4,"evidence":[
  {"channel":"planner","statement":"The move is reversible and history-independent, but success requires coordinating two agents that cannot be repaired independently."},
  {"channel":"proof","statement":"No hidden state or depletion is involved; closure requires a coupled change across two separated subgoals."},
  {"channel":"compiler","statement":"Each node is fully observed and transformations commute, yet the valid optimization requires changing producer and consumer together."}]},
 {"id":5,"evidence":[
  {"channel":"proof","statement":"A hidden metavariable assignment distinguishes states that print the same, and closure also requires a coordinated change across two subgoals."},
  {"channel":"compiler","statement":"Alias provenance is omitted from the local view, while the successful rewrite must alter both producer and consumer."},
  {"channel":"planner","statement":"Two locally identical worlds hide different reservations and the repair requires synchronized actions by two agents."}]},
 {"id":6,"evidence":[
  {"channel":"compiler","statement":"The outcome depends on pass order and the valid repair must coordinate producer and consumer, but no resource is consumed."},
  {"channel":"planner","statement":"Earlier commitments alter the effect of the same visible move, and resolution requires synchronized changes across two agents."},
  {"channel":"proof","statement":"A tactic's effect depends on prior normalization history and closure requires a coupled change across separated subgoals."}]},
 {"id":7,"evidence":[
  {"channel":"proof","statement":"A hidden assignment distinguishes printed-identical states; prior tactic order matters; two subgoals must change together; and a linear hypothesis is consumed."},
  {"channel":"planner","statement":"Hidden reservations, action history, multi-agent coupling, and one-use budget consumption all affect the same decision."},
  {"channel":"compiler","statement":"Alias provenance is hidden, pass order matters, producer and consumer must change together, and ownership permission is spent."}]},
 {"id":8,"evidence":[
  {"channel":"proof","statement":"The state is fully observed and history-independent, but using the step consumes a hypothesis that cannot be restored."},
  {"channel":"compiler","statement":"No alias ambiguity or order effect exists; the transformation irreversibly spends an ownership permission."},
  {"channel":"planner","statement":"The current world is fully visible and action order is irrelevant, but the move consumes a nonrenewable token."}]},
 {"id":9,"evidence":[
  {"channel":"compiler","statement":"A hidden alias tag and pass-order history both matter, but the rewrite is reversible and uses no scarce permission."},
  {"channel":"planner","statement":"Invisible reservations and earlier commitments jointly distinguish otherwise identical states, without resource depletion."},
  {"channel":"proof","statement":"Printed state omits a metavariable assignment and prior normalization history matters; no linear resource is consumed."}]},
 {"id":10,"evidence":[
  {"channel":"planner","statement":"All state is visible and history does not matter; the only obstruction is that two agents must alter their choices jointly."},
  {"channel":"compiler","statement":"There is no hidden aliasing or order sensitivity; only a producer-consumer coupled rewrite is required."},
  {"channel":"proof","statement":"The proof state is fully represented and tactics commute, but two separated subgoals require one coordinated construction."}]},
 {"id":11,"evidence":[
  {"channel":"proof","statement":"Printed states hide a relevant assignment and a linear hypothesis is consumed, but tactic order is otherwise irrelevant and the repair is local."},
  {"channel":"compiler","statement":"Alias provenance is hidden and ownership is one-use, while pass history and cross-node coupling are irrelevant."},
  {"channel":"planner","statement":"A hidden reservation and nonrenewable budget matter, but neither sequence nor multi-agent coordination does."}]},
 {"id":12,"evidence":[
  {"channel":"compiler","statement":"Pass order matters and ownership permission is consumed, while the state is fully observed and the rewrite stays local."},
  {"channel":"planner","statement":"Earlier commitments change the move and a token is spent, with no hidden variables or multi-agent coupling."},
  {"channel":"proof","statement":"Prior normalization history changes continuation and a linear hypothesis is used up, but the printed state is complete and one subgoal suffices."}]},
 {"id":13,"evidence":[
  {"channel":"planner","statement":"A hidden reservation matters and two agents must coordinate; action history and resource depletion do not."},
  {"channel":"proof","statement":"An omitted assignment distinguishes states and two subgoals must change together, with no order dependence or linear use."},
  {"channel":"compiler","statement":"Alias provenance is hidden and producer-consumer coupling is required, but transformations commute and are reversible."}]},
 {"id":14,"evidence":[
  {"channel":"proof","statement":"Prior tactic order matters, two subgoals must change together, and a linear hypothesis is consumed; the visible state itself is complete."},
  {"channel":"compiler","statement":"Pass history, producer-consumer coupling, and one-use ownership all matter, without hidden alias state."},
  {"channel":"planner","statement":"Sequence, multi-agent coupling, and nonrenewable budget matter, while current observations are complete."}]},
 {"id":15,"evidence":[
  {"channel":"compiler","statement":"The visible IR is complete, transformations commute, the rewrite is local, and no ownership permission is consumed."},
  {"channel":"proof","statement":"The printed state contains everything relevant, tactic order is immaterial, one subgoal changes locally, and no linear hypothesis is spent."},
  {"channel":"planner","statement":"The world is fully observed, history-independent, independently repairable, and resource-renewable."}]}
]

# Frozen semantic ontology invented from EVIDENCE only.  No downstream domain or
# labels were available when this is frozen.
FROZEN_SPEC = {
 "dimensions": [
  {"name":"latent-state incompleteness","positive":"apparently identical current states hide verifier-relevant internal state"},
  {"name":"path dependence","positive":"future effect depends on the trajectory/order that reached the current visible state"},
  {"name":"coupled intervention","positive":"successful repair requires coordinated change across otherwise separable components"},
  {"name":"consumptive irreversibility","positive":"an action spends a one-use resource/permission so the transition is not freely reversible"}
 ],
 "encoding_order":["latent-state incompleteness","path dependence","coupled intervention","consumptive irreversibility"]
}

# Semantic encodings inferred from the residual fields under the invented ontology.
FROZEN_K = {
 0:(0,1,0,1), 1:(1,0,0,0), 2:(0,1,0,0), 3:(1,0,0,1),
 4:(0,0,1,0), 5:(1,0,1,0), 6:(0,1,1,0), 7:(1,1,1,1),
 8:(0,0,0,1), 9:(1,1,0,0), 10:(0,0,1,0), 11:(1,0,0,1),
 12:(0,1,0,1), 13:(1,0,1,0), 14:(0,1,1,1), 15:(0,0,0,0)
}
