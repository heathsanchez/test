# Unified Consequential Runtime — evidence-bound native development

**Status: native certificate repair + cross-repository operational admission qualified.**
**Scientific autonomous method genesis and system-wide L7 remain UNKNOWN.**

This branch integrates *the actual qualified programs* that already existed in
MathGraph, MSI, RealityGraph / FLASH, Metatron and the original research repos.
It does not invent another finite O1/O2 world or treat a green workflow as a
scientific result. Source repositories and the production MathGraph website
are unchanged. [Draft PR #123](https://github.com/heathsanchez/test/pull/123)
is intentionally unmerged.

## New independent native checker result

The prior pinned [V10 native failure](https://github.com/heathsanchez/test/actions/runs/38237298379)
was a generated CSLib proof that did not elaborate at actual Lean 4.35.0-rc4:
missing \`fin_cases\` support and an unsolved simulation obligation. It was
not a theorem that the target was expressively impossible.

[**New CSLib native qualification #38466549740**](https://github.com/heathsanchez/test/actions/runs/38466549740)
at \`dd0d53ff3ce198aaac9f4537f418682efd6a3f79\` is green.
[Sealed original artifact #11848853826](https://github.com/heathsanchez/test/actions/runs/38466549740/artifacts/11848853826)
has ZIP SHA-256
\`76c842791e428dcd9263a2b9282c9d0f27ed61e748f8b340541f91239f6f5bb8\`.

It reuses original, *unchanged* V10 Python fixed-point solver
\`heathsanchez/test@a50f1990:capstone/v10/run.py\`, frozen six declared LTS
cases and independent reference. It constructs six Lean proof files,
compiling source-specific simulation and bisimulation certificates with
\`Mathlib.Tactic.FinCases\` and \`simp_all\` against
\`leanprover/cslib@4b88bcac4c0dec65b3f45b59e85f5397045efd8d\`.
Four seed-pair positive certificates and two seed-pair refutations are
native-checked; actual missing relations remain refuted. A deliberately
forged universal simulation theorem is not accepted, but the failed tactic
attempt is NOT evidence of a general semantic impossibility. The original
sealed artifact's \`proof_backend\` label is imprecise (it says "decidable
reflection"); the effective successful source backend is the actual imported
\`fin_cases\` + simplification procedure. The checked Lean files are primary.

**Narrow scientific meaning:** an existing finite solver, equipped with a
source-specific target-language proof backend, passed an external native
checker where its previous generated certificates failed. Neither arbitrary
method invention nor an independently open theorem has been demonstrated.

## New event-to-native research-state integration

[**Source-event integration #38469251893**](https://github.com/heathsanchez/test/actions/runs/38469251893)
at \`7571513b11d9c7b9839abe0d8b252b2015aed747\` is fully green.
[Sealed integrated artifact #11851366033](https://github.com/heathsanchez/test/actions/runs/38469251893/artifacts/11851366033)
has SHA-256
\`5743785f8c775db0cbeb589dadc86b6baf0e5377416cfbdc78cf28b4fea3e83b\`.

The workflow independently fetches the actual successful native run,
checks its *source commit and independent GitHub artifact digest*, rechecks
each proof SHA against the sealed manifest and the original source-bound
semantic reference, and constructs a real \`ExternalEventEnvelope.capability\`
using the existing RealityGraph FLASH library. The event identity is
\`cslib:cycle:native-source-checked-simulation:v1\`. Native theorem
origin \`dd0d53f...\` and emitter implementation \`4543d75...\` are separate
pinned identities; they are NOT incorrectly collapsed to the current
coordinator revision.

Existing real-source events from Lean kernel, MSI ARC, Collatz (two
independent historical source commits) and SAIR survive unchanged.
The genuine FLASH closure has **6 events, 4 active scoped capabilities,
2 original obstructions**. A second-source deletion ablation removes
only the new native capability. A deliberately simulated typed capability
revocation causes that capability to cease being active, **reopens the
native obligation**, preserves all three old capabilities and both
original obstructions, and is discarded afterward rather than being
misrepresented as an actual source withdrawal. The integration also verifies
independent cold restore, state replay and Metatron append-only liveness.
Metatron recorded **29 total nodes, 25 live, 22 existing prior IDs retained**
in the first fully green native integration.

**Important support semantics:** FLASH \`support_ids\` represent
*dependency parent capability IDs*, not external Lean receipt identifiers.
The native verified event is a root with no other capability parents.
Its original source, exact checked proof, GitHub receipt and assumptions
are bound separately by the event evidence SHA, \`certificate_id\`,
\`provenance_ids\` and Metatron evidence lineage.
External source revocation must be encoded by a new explicitly checked
typed revocation event, not by silently asserting a proof token is an
executable dependency. A simulated revocation does not establish automatic
monitoring of upstream revocations.

## Real MathGraph and research evidence retained

Two unchanged implementation-independent MathGraph consumers are executed:
a \`QUALIFIED_BOUNDED\` finite capability replay with
\`current_applicability=UNKNOWN\` and \`action_authorization=NONE\`,
and an exact source-index catalogue publication replay of 2,345
declaration occurrences / 3,571 structural edges / 13 pinned Mathlib
modules. SOURCE_INDEXED is **not** Lean proof replay. MathGraph source
indices retain \`independent_verification=NOT_CHECKED\`, and authorization
\`NONE\`. Prior MSI/MDA/Metatron and negative native runs remain
source-pinned historical evidence, never self-certifying inventions.

The workflow stores its closure report, FLASH state bundle, Metatron
append-only log, new qualified source event, native original proof files
and independently checked history in one artifact. New runs restore
only from a **completed-successful** previously qualified integration,
not merely the newest available artifact from a failed job.

## What is still genuinely missing

These remain UNKNOWN, not retrospectively turned into PASS:
- source-derived *new semantic method*, not a human-authored tactic fix;
- previously open **source-distinct independent native** target repaired
  without target-specific human engineering;
- verified generator change producing a second independent native
  research capability, including held-out transfer and deletion ablation;
- measured full acquisition+verification+maintenance economics against
  equally informed competent baselines;
- production freshness, source authenticity, ACT authorization, and
  an independent outside-owner consumer;
- complete mechanization of the broader CLC formal specification.

The next real scientific attempt must attack one of those missing native
semantic boundaries *through this already working infrastructure*, without
another locally chosen finite experiment masquerading as L7.

Workflow: \`.github/workflows/unified-consequence-runtime.yml\`.
Native source checker:
\`.github/workflows/unified-cslib-native-continuation.yml\`.
Native event adapter:
\`research/unified_consequence_runtime/native_proof_event.py\`.
Coordinator:
\`research/unified_consequence_runtime/integrate.py\`.
Source policy:
\`research/unified_consequence_runtime/native_policy.json\`.

**Declared verdict: WARRANTED_BOUNDED_NATIVE_CERTIFICATE_AND_OPERATIONAL_REUSE,
not E2E-SYSTEM autonomous intelligence.**
