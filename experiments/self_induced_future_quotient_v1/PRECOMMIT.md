# Self-Induced Future Quotient V1 — frozen precommit

## Question
Can a fixed LLM, given only raw verified observations, a target, and available interventions, construct a compact intermediate representation that preserves the future-action distinctions needed to choose the right query, approaching the performance of a hand-supplied target-relative quotient?

## Frozen task family
Reuse the exact deterministic task generator and seed from Target Quotient Right Question V1: 48 protected tasks, 16 each for mod 2, 3, and 5 additive latent worlds, with gauge X=0. Each task has partial verified observations, one target, and four allowed extra queries. Python exactly enumerates the surviving hypothesis set and computes the target-entropy-optimal query.

## Arms
1. RAW_DIRECT: choose the query directly from raw observations.
2. SELF_INDUCED: two calls. Call A sees raw observations/target/queries and must construct a compact reusable decision representation without selecting/ranking a query. Call B sees only that representation plus target/query names and selects the query.
3. HAND_QUOTIENT: receives the exact target-relative query-outcome -> target-outcome count tables established in the previous experiment.
4. SHAM_MARGINAL: receives query and target marginals but not their coupling.
5. OPTIMAL_QUERY: deterministic external ceiling.

## Primary
SELF_INDUCED must beat RAW_DIRECT on both exact optimal-query rate and downstream target accuracy.

## Strong success
SELF_INDUCED exact optimal-query rate >= 0.80 and downstream target accuracy >= 0.90, while HAND_QUOTIENT remains >= 0.90 optimal and SHAM_MARGINAL does not match SELF_INDUCED.

## Mechanistic measurements
Record representation text, exact chosen query, optimal-query rate, downstream target accuracy, target entropy after query, information-gain regret, and a blinded representation-fidelity diagnostic computed externally by checking whether the induced representation text explicitly captures query-outcome-conditioned consequences for the target (diagnostic only; not part of primary).

## Interpretation
- SELF > RAW with high transfer: evidence that the model can construct useful future-relative state rather than merely consume it.
- SELF ~= RAW but HAND >> both: quotient representation is useful but remains externally scaffolded.
- SELF > SHAM but below HAND: partial autonomous representation induction.
- Surprise: preserve as a new residual.

No protected outcomes are to be inspected before this precommit exists.