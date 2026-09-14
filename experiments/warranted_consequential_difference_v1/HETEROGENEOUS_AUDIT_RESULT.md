# WCD V1 — Heterogeneous Domain Audit Result

**Frozen WCD kernel:** `978af4e94815128b4c517562f9a0bae26eea1e55`  
**Frozen adapter manifest:** `c884b39c67f7f30499a3ee4eafb50a8e88c394cb`  
**Observations commit:** `5793ad51c6fc3661e54da3ed5b1ce191fcf37a44`  
**Adjudicator commit:** `a0f5009daa0625c5e3ea96e60c74a7a462e0ffc4`  
**Workflow commit:** `a3f25ac532d1fe0bc59c4644e6e64ae19a2c877c`  
**Workflow run:** 34817858122  
**Workflow job:** 103892372888  
**Artifact:** 10336454206  
**Artifact digest:** `sha256:8f772bec3f66f2704b6f94d156c69eda9f265dfe3e7ea551bb3854d82ca831a8`

## Verdict

```text
PASS 23/23
SURVIVED_HETEROGENEOUS_DOMAIN_AUDIT_WCD_V1
NO_HETEROGENEOUS_COUNTEREXAMPLE_FOUND_UNDER_FROZEN_ADAPTERS
```

CI first proved both the WCD kernel and the heterogeneous adapter manifest unchanged since their respective freeze commits. It then replayed controller V9 invariants and the 31/31 dedicated finite WCD falsification suite before the heterogeneous adjudication.

## Domain results

### D1 — Lean Kernel Arena E0034 parent-tail splice

All A0/A1/ablation arms passed the frozen semantic corpus:
- 103/103 good accepted;
- 58/58 bad rejected.

Thus the arms are semantically equivalent under the frozen Arena ground.

Primary paired CPU:
- A0: 0.769054 s
- A1: 0.782212 s
- ablation: 0.770841 s

A1 was +1.711% slower than A0. The experiment's frozen interpretation said a CPU regression rejects the change.

WCD form:

```text
EQ + PREFERENCE -> reject A1 / carry present
```

### D2 — Vero blind proof-interface regenesis

The amputation caused a real protected failure and exact re-ablation also restored failure, so a consequential distinction existed.

However the proposed regenerated continuation failed frozen lawfulness/ground gates:
- agent_completed = false;
- only_allowed_file_changed = false;
- ring_verifies = false.

The workflow classified the experiment as FAIL / RESIDUAL and did not promote the candidate.

WCD form:

```text
DIST observed, but candidate unlawful -> residual / no inheritance
```

### D3 — Target Quotient Right Question

Calibration-only in this audit because the result had been inspected earlier.

Protected pooled results:
- OBS_ONLY accuracy 0.7083, optimal-query 0.3542;
- SHAM_MARGINAL accuracy 0.5417, optimal-query 0.2917;
- TARGET_QUOTIENT accuracy 1.0000, optimal-query 0.9583.

WCD form:

```text
DIST -> retain target-relative outcome-to-target coupling in scope
```

### D4 — Research Controller V9

Original invariant suite replayed green.

Frozen adapter reproduces:
- complete matching pre-outcome signatures -> EQ;
- complete differing signatures -> DIST;
- protected-outcome access -> UNKNOWN;
- unfrozen equivalence protocol -> UNKNOWN;
- incomplete probe coverage -> UNKNOWN.

WCD form:

```text
EQ | DIST | UNKNOWN
```

This sharpens the original controller's binary equivalent/not-equivalent API by distinguishing genuine difference from insufficient authority.

### D5 — Andrews–Curtis competitive publisher

Retrospective evidence available before the heterogeneous adapter freeze:
- 8 optimized candidates;
- 8 verifier-clean candidates;
- proof-atlas fortification saved 402 moves internally;
- strict public-frontier wins after fortification: 0;
- selected rows: 0.

WCD form:

```text
GROUND-VALID + NO PREFERENCE WIN -> identity / carry incumbent
```

Validity alone did not authorize publication.

## Cross-domain result

The five domains exhibited at least five distinct WCD forms rather than one generic success story:

1. semantic equivalence plus preference;
2. consequential difference with an unlawful candidate;
3. protected consequential difference;
4. explicit EQ/DIST/UNKNOWN epistemic relation;
5. semantic validity with no preference win.

No tested transition required adding an observable after the adapter freeze.

## Claim boundary

This result supports:

> The frozen WCD candidate represented every tested developmental transition under independently frozen domain consequence interfaces.

It does **not** prove universality.

Three of the domain families (Lean E0034, proof regenesis, controller V9) were historical outcomes not opened in this audit until after their adapters were frozen. Target Quotient was calibration-only. The ACC evidence was explicitly retrospective.

The strongest remaining test is prospective: freeze a domain adapter before a genuinely new developmental episode occurs, then let the unchanged WCD candidate predict whether the resulting change should split, merge, remain unknown, or be rejected/retained by preference.
