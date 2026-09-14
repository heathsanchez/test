# WCD V1 Heterogeneous Domain Audit — Frozen Adapter Manifest

**Frozen kernel:** `experiments/warranted_consequential_difference_v1/FROZEN_CANDIDATE.md` at `978af4e94815128b4c517562f9a0bae26eea1e55`.

**Purpose:** Try to falsify the frozen WCD candidate on pre-existing domain experiments that were not designed around WCD.

This manifest is frozen before the selected protected run logs are opened for this audit. The WCD kernel itself may not be edited.

## Common decision rule

For each domain, the adapter freezes three things *before* the selected outcome is read:

1. **Ground:** independent semantic correctness / validity authority.
2. **Authorized consequence/measurement interface:** the outcomes allowed to justify a developmental distinction.
3. **Preference:** allowed ordering over candidates that already satisfy ground.

A historical retained/rejected transition is WCD-representable only if, under this frozen interface, it is one of:

- `DIST`: candidates differ on warranted ground/protected future consequence;
- `EQ + PREFERENCE`: candidates are ground-equivalent but a declared measurement/preference orders them;
- `UNKNOWN`: authority is insufficient to merge/split/promote;
- `FRONTIER`: multiple lawful incomparable candidates remain.

**Falsifier:** a verified/required developmental transition whose retention is necessary for the experiment's protected future outcome but which cannot be justified by any frozen ground/consequence/preference difference below. Do not add an observable after reading the outcome.

---

## D1 — Lean Kernel Arena E0034 parent-tail splice

**Evidence source:** workflow `.github/workflows/lean-kernel-arena-a6-e0034-tail-splice.yml`; selected run = the workflow run associated with the experiment's launch/implementation history, without outcome-based cherry-picking.

**Objects:** checker implementations `a0`, `a1`, `abl`.

**Ground:** frozen Arena corpus:
- every good case accepted;
- every bad case rejected.

**Authorized developmental measurements:** median CPU and wall time on the frozen dominant `grind-ring-5` case under the paired/interleaved protocol.

**Preference:** among ground-equivalent arms, lower paired CPU; wall time is supporting measurement.

**WCD prediction:**
- correctness divergence => `DIST` and reject invalid arm;
- identical correctness => semantic `EQ` under the frozen corpus;
- a retained optimization must be justified as `EQ + PREFERENCE`, not as a new semantic distinction.

**Falsifier:** the optimization is retained/necessary although it changes neither frozen ground nor declared resource preference.

---

## D2 — Vero Blind Proof Interface Regenesis V1

**Evidence source:** workflow/script family `vero-blind-proof-interface-regenesis-v1` / `.github/scripts/vero_blind_proof_interface_regenesis_v1.py`; selected run = experiment run, no outcome cherry-picking.

**Objects:** amputated proof present, regenerated-interface present, exact post-ablation present.

**Ground:** Lean verification of `Galoistools/Proof/Ring.lean` plus full `lake build`, with frozen proof-hygiene and allowed-edit gates.

**Authorized consequence:** whether the four unchanged consumers compile/verify while the regenerated slot obeys hygiene/provenance restrictions.

**Preference:** no extra preference is needed for the primary claim; smallest allowed edit surface is part of the frozen lawfulness constraint.

**WCD prediction:**
- amputation vs successful regenesis => warranted `DIST`;
- exact re-ablation must restore failure if the regenerated distinction is causal;
- regeneration is retained only if those protected consequences differ.

**Falsifier:** a regenerated interface is necessary/verified but exact ablation leaves every authorized consequence unchanged.

---

## D3 — Target Quotient Right Question V1

**Evidence source:** frozen precommit + protected workflow run for `target-quotient-right-question-v1`.

**Objects:** OBS_ONLY, TARGET_QUOTIENT, SHAM_MARGINAL, RANDOM_QUERY, OPTIMAL_QUERY.

**Ground/authorized consequence:** exact Python enumeration of compatible latent worlds; downstream target accuracy; exact optimal-query rate; target entropy/regret.

**Preference:** frozen primary thresholds and comparisons from PRECOMMIT.md.

**WCD prediction:** the target-relative quotient is retained only if its outcome-to-target coupling creates a protected consequential difference versus OBS_ONLY and the sham that removes the coupling.

**Falsifier:** quotient/coupling is retained despite no protected consequence difference, or a protected consequence difference exists but the adapter merges the arms.

**Status:** calibration-only in this audit because its result was inspected earlier.

---

## D4 — Research Controller V9 outcome-blind move equivalence

**Evidence source:** `experiments/controller_v9/README.md`, `equivalence.py`, `test_equivalence.py`, workflow `controller-v9.yml`.

**Objects:** candidate moves from different generators/provenances.

**Ground/authorized consequence:** probe suite frozen before protected outcomes; each move's allowed outcome set/signature on those probes.

**Warrant rule:**
- complete frozen matching signatures => `EQ` for attribution;
- a pre-outcome signature difference => `DIST`;
- protected-outcome access, unfrozen protocol, or incomplete probe coverage => `UNKNOWN`, never forced equivalence.

**Preference:** none for equivalence attribution.

**WCD prediction:** outcome-blind behavioral equivalence must match the three-way `DIST/EQ/UNKNOWN` discipline without using later terminal success to rewrite classes.

**Falsifier:** the controller's valid attribution requires post-hoc equivalence not representable under the frozen probe relation.

---

## D5 — Andrews–Curtis competitive publication

**Evidence source:** `.github/workflows/acc-reset-publisher.yml`; selected evidence = latest completed publisher authority available after this manifest commit if one exists during the audit, otherwise latest completed authority before freeze, explicitly labeled retrospective.

**Objects:** candidate Andrews–Curtis move sequences.

**Ground:** pinned official verifier replay.

**Authorized measurement:** move/path length and live public frontier/quota state.

**Preference:** only verifier-clean **strict** improvements may be published; ties and non-strict rows are excluded.

**WCD prediction:**
- invalid vs valid paths => `DIST` at ground;
- valid paths with the same solved endpoint are semantically equivalent for validity but developmentally ordered by declared path-length/frontier preference;
- ties remain unpromoted under the frozen publication rule.

**Falsifier:** a published row is neither a verifier-clean strict improvement nor justified by any frozen preference dimension.

---

## Pass/claim rule

This audit may only claim:

> The frozen WCD candidate represented all tested transitions under independently frozen domain consequence interfaces.

It may NOT claim universality.

Any domain falsifier above ends the V1 universal-candidate claim or forces an explicit scope restriction.
