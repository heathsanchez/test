# Formal correspondence and remaining obligations

The executable integration has bounded native evidence. It is not currently a
concrete Lean instance of the MathGraph Verified Developmental Navigation (VDN)
or MSI formalizations. Native consequence checks, causal support closure and
generic formal theorems establish different facts; no refinement theorem has
yet connected the Python implementation to those Lean definitions.

The frozen integration protocol is [DEVELOPMENTAL_PROTOCOL.md](DEVELOPMENTAL_PROTOCOL.md).
Its executable sources are E/D `heathsanchez/test@c9092fa57c8943e638f95689cd36e6a63310f41e`,
Metatron `metalogiclabs/metatron@b9d1b5cc10477188be6e55617699be60e70f6dad`,
FLASH `heathsanchez/realitygraph@50c43b14e7272469bc51ff7204dec07682a996d7`,
and native evaluator `ServiceNow/webarena-verified@6473f72db5dcefc97b5725b59e734504edc28a21`.
The archive, exact file and task hashes are in [developmental_sources.json](developmental_sources.json).

## MSI conditional results

The exact source pin is `heathsanchez/Minimal-Sufficient-Interface@5d448c0ecc82ff3945d009963064ebbb67d2f308`.
These source assumptions were inspected directly using the pinned local Git
objects, with cross-checks from the MSI archaeology agent. They are
specifications to instantiate, not runtime guarantees already proved.

| Source theorem | Required assumptions | Runtime obligation still open |
| --- | --- | --- |
| `BehaviouralCongruence.greatest_invariant` | An `ActionMonoid` satisfying identity, associativity and action laws; an invariant relation compatible with observations. `BehEq` quantifies over every future action. | Define actual runtime actions and observable consequences, prove action laws and relation invariance, and quantify over the intended continuation language. A finite test set is not that quantifier. |
| `BehaviouralCongruence.finite_recovery` | A finite list covering every action; an empty initial sequence; a genuine refinement step whenever the sequence is nonterminal. The stated bound is at most the list length. | Supply a complete finite action carrier and lawful refinement process. The integrated task set does not cover arbitrary future actions. |
| `TypedBehaviouralCongruence.greatest_congruence` | A lawful small category, lawful typed action, categorical congruence and observation compatibility. Typed behavioral equality covers all typed future observations. | Give typed interfaces, category/functor laws, and correspondence between executable composition and formal composition. |
| `DevelopmentalCategory.extension_refines` / `new_separator_forces_split` | Inclusion of allowed continuations in a fixed ambient category; a split additionally needs an old equality and a new allowed continuation whose observations differ. | Show the acquired executable representation really extends the allowed continuation family and supply the distinguishing consequence. Changes to the ambient state/observation language need a separate model. |
| `ResidualRegimeBridge.residual_to_minimal_regime_and_capability` | A lawful `ActionMonoid` and a genuine old-kernel collision separated by a new kernel. The construction refines by intersecting the old relation with the new consequence kernel. | Supply the actual old observational equivalence, new consequence and collision witness. `CanDescend` concerns a consequence into the observation codomain; it does not prove every state transition descends. |
| `MinimalRepair.minimal_justified_repair` | The abstract `MeetKernel` laws in `Kernel.lean`. | Instantiate those laws and the refinement order before asserting least or minimal repair for implementation states. |

`greatest_invariant` and `greatest_congruence` do not require the competing
relation itself to be an equivalence relation. `MeetKernel` requires an
idempotent, commutative and associative meet; `Le a b` means `meet a b = a`.
`MeetKernel.update_cannot_coarsen` proves that a meet update cannot genuinely
retract constraints. Runtime withdrawal therefore belongs to the recorded
provenance and recomputation layer, rather than being an instance of monotone
meet refinement. `EquivalentOn.antitone_basis` gives the separate conditional
law for removing protected continuations from an observation basis.

`BlindRecursiveCrossGrammarGenesis.lean` checks frozen finite Boolean programs
(eight input triples, plus a six-bit exhaustive certificate), not an arbitrary
Python runtime. Its deleted-carry equality compares cut execution to isolated
protected additions; a separate evidence check is needed for any claimed
performance loss. No universal runtime implementation theorem follows.

## Operational interpretation

Original E induction supplies a grouped representation from the archived
shopping-admin observation and task 63; the native WebArena evaluator checks
regenerated responses. Metatron retains source and consequence dependencies;
FLASH reclosure provides a second operational support-liveness calculation.
The coordinator supplies a thin executable adapter. This gives concrete
candidate objects for a future formal model, but their Lean types and laws
have not been proved.

Support withdrawal and restoration change which historical consequences can
be warranted through their recorded provenance. They do not change the truth
of an independently checked proposition, nor establish upstream revocation
monitoring. Cold replay checks retained executable behavior for the declared
snapshot; it does not establish fresh observation or every future continuation.

## VDN exact source and certificate obligations

Exact inspected source: `metalogiclabs/mathgraph@cf359686c74549a132c7a651cd7aabc7c1a870fe`,
`verified-developmental-navigation/lean/VerifiedDevelopmentalNavigation/DevelopmentCertificate.lean`
(Git blob `3f6ea923d0b3f0727bffcf9b6fd1bb1d975cc466`), its imported
`VerifiedDevelopmentalNavigation.lean` (blob `e64adf542ba321efbf74787974fa5c5bae795da5`),
and `Routing.lean` (blob `abe4f8053d438a6ef596c2cfa37699333046ad8e`).
These exact GitHub source objects were recovered and read; Lean was not
recompiled in this session.

`CapabilityPhaseChangeCertificate` fixes two worlds over the same state,
context and observation types, allowing different action types. It requires
an explicit old trace boundary, a finite list covering every trace satisfying
that boundary, proof that every listed old trace fails to reach the target,
an action embedding preserving every old step at every state, and a new-world
reachability witness. `old_unreachable_within` proves only boundary-relative
nonreachability; `phase_change` combines that with the new witness.
`retains_old_capability` follows from the step-preserving action extension.
This retention theorem concerns reachability; it does not by itself establish
that changed observation interfaces preserve behavioral quotients.

The runtime supplies actual native success witnesses and scoped causal
withdrawal checks. It does **not** currently supply a Lean `World` instance,
a complete cover of its old executable trace language, checked failure for
that cover, or a step-preserving action embedding. Original grouping ablation
and failed search therefore remain native negative controls, never complete
old-language impossibility certificates. Formal phase-change qualification
for this concrete Python machine remains **UNKNOWN**.

`Routing.route_complete` is a classical logical case split over `CanAct` and
`CanProbe`, not a computable general search algorithm. `extend_questions_sound`
is relative to the declared admitted probe family. Its resolving-probe and
extension lemmas require an independently supplied proof that the new probe
resolves every outcome cell. No such universal runtime proof is asserted here.

The archaeology record is `/workspace/archaeology/formal/INDEX.json`.
Native kernel/arena source is separate from VDN: Arena checker acceptance uses
its configured Lean environment and permitted axioms, and neither a source
index nor a green workflow alone establishes proof replay.

General autonomous generator invention, unrestricted developmental completeness
and system-wide L7 remain **UNKNOWN**. There is no general intelligence claim.
