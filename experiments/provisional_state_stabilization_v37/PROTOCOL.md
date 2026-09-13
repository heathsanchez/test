# Provisional State Genesis and Stabilization V37 — Frozen Protocol

## Question

Can a developmental system separate two evidentiary thresholds that V36 exposed?

1. **Genesis:** consequence already forces a new residual state to exist.
2. **Stabilization:** there is enough future authority to warrant that state's recurrent outgoing transitions.

V37 tests whether a newly forced state can be constructed provisionally without pretending that its recurrence is already known, and whether additional consequence evidence later stabilizes the same state structure without changing the scientific kernel.

## Frozen substrate

The raw encounter remains a finite ordered binary string with no supplied macro-token boundaries.

The bounded tokenizer class is inherited from V36:

- anonymous prefix-free codebooks;
- 1 to 3 token types;
- codeword length 1 to 3;
- full raw-string parsing required.

This experiment is **not** primarily a tokenizer-genesis claim. Tokenization is retained as the substrate in which the V36 residual arose.

The developmental object is a partial recurrent residual machine over the induced anonymous token sequence.

## Residual signatures

For a complete consequence table through token depth N and an admitted distinguishing horizon h,

    R_h(p) = ( C(p ++ s) )_s

for every suffix s of length at most h for which the complete table guarantees p ++ s.

A residual state is **born** when a distinct R_h signature is required by observed future consequence.

A transition from state q under anonymous token a is **stabilized** only if there exists at least one representative prefix p of q with enough remaining authority to identify the full horizon-h residual signature of p ++ a, and all such supported representatives agree.

If a state is consequence-distinct but has no representative with enough remaining authority to certify its outgoing transitions, the state is retained as:

    PROVISIONAL

rather than deleted and rather than assigned an invented recurrence.

## Horizon selection

The kernel searches h from weakest to stronger future views.

For each h:

1. construct all consequence-distinct residual signatures supported by the complete table;
2. inspect every state having at least one representative with enough authority for an outgoing transition;
3. reject h if supported representatives of the same residual state disagree on any successor residual;
4. otherwise admit the quotient.

The first admitted h is the minimum future horizon needed to make every **currently warrantable** transition deterministic.

This allows a state to be born at the evidence frontier while withholding unsupported recurrence.

## Stable versus provisional result

A candidate is:

- VERIFIED_STABLE when every discovered residual state has all outgoing transitions warranted;
- VERIFIED_PROVISIONAL when at least one discovered state is consequence-distinct but one or more outgoing transitions remain unsupported;
- UNKNOWN when authority is incomplete;
- no construction is authorized when verification is disabled.

A provisional result is explicitly **not** executable beyond its warranted transition frontier.

## Post-freeze challenge family

After the scientific core is frozen, the evaluator may supply hidden recurrent consequences at staged authority depths.

Primary separators will include:

- a three-token absorbing relation whose new fourth state is first born before its recurrence can be certified;
- a longer four-token absorbing relation with a larger birth-to-stabilization gap;
- already-stable controls such as parity and a shorter relation;
- raw-bit relabellings;
- held-out longer sequences tested only after stabilization.

The kernel is not told which family is being tested.

## Frozen gates

G1. Frozen scientific core is byte-identical after hidden staged worlds are committed.
G2. The three-token relation at the shallower authority depth returns VERIFIED_PROVISIONAL.
G3. That shallow result already contains the independently expected four consequence-distinct residual states.
G4. Exactly the frontier-born state lacks warranted recurrence in the shallow three-token case.
G5. The same three-token relation at one additional authority depth returns VERIFIED_STABLE.
G6. The stabilized result retains the same residual signature set as the provisional result.
G7. The stabilized three-token machine exactly transfers to a longer held-out horizon.
G8. The hidden tokenizer/codebook is unchanged across genesis and stabilization stages.
G9. A four-token relation exhibits the same qualitative sequence: expected state birth first, stable recurrence only later.
G10. The four-token provisional result contains the independently expected five residual states.
G11. The stabilized four-token machine exactly transfers beyond the stabilization horizon.
G12. An already-stable parity control is not mislabeled provisional.
G13. A shorter two-token relation stabilizes earlier than the three- and four-token relations.
G14. No provisional result is reported as an executable stable recurrent machine.
G15. Raw-bit complement relabelling preserves birth/stabilization status and canonical residual structure.
G16. Incomplete authority remains UNKNOWN_AUTHORITY.
G17. Verifier ablation authorizes no residual construction.
G18. The frozen kernel contains no hidden challenge pattern, semantic family name, or hard-coded authority depth.
G19. Minimum distinguishing horizons increase with the hidden relational depth as independently expected.
G20. Birth and stabilization thresholds are distinct in at least two hidden families.

## Claim boundary

A pass would establish a narrow but important developmental distinction:

> within the frozen finite residual-machine and tokenizer substrate, consequence can force a new representational state before there is enough evidence to warrant its persistence law; the system can preserve the state provisionally and stabilize it only when later consequence closes the recurrence obligation.

A pass would **not** establish general Bayesian uncertainty, unrestricted concept formation, or biological development.

The scientific implication tested here is only that:

    genesis obligation != retention/recurrence obligation

and that the verifier can keep those obligations separate.
