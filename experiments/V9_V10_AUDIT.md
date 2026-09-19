# V9/V10 developmental version-space audit

## V9 bounded causal policy test

V9 compares premature single-story collapse with preservation of a live developmental version space over four supplied rival regime changes.

Result on GitHub Actions:

- SINGLE protected-transfer correctness: **2/4**.
- TOP-K/version-space correctness: **4/4**.
- TOP-K recovered the hidden regime: **4/4**.
- Mean TOP-K separator probes: **2.25**.

Interpretation: when the initial residual field is genuinely ambiguous, committing to the highest-prior semantic story can produce wrong downstream action even after one local falsification. Preserving rivals and selecting probes by expected version-space reduction eliminates that failure in the bounded world.

Claim boundary: the four hypothesis families and their probe signatures are supplied. This is a controller-policy test, not open-ended hypothesis invention.

## V10 sealed historical MathGraph replay

Stage1 selected checkpoint `3713a4a0a8e3da67fc41c953861a06fcc3439e3c` from 32 eligible dense checkpoints using only preceding history. The frozen top-5 version space, committed before reveal, ranked:

1. scheduler / priority refinement;
2. Reason-Atlas-conditioned operator construction;
3. persistent multi-episode compounding;
4. representation / continuation abstraction;
5. verification / promotion hardening.

The single-story baseline was rank 1: scheduler / priority refinement.

After freeze, stage2 revealed the next five commits:

1. `Add compounding Lawbook engine v0`
2. `Add real SAIR compounding benchmark`
3. `Add production Lawbook admission gate`
4. `Add multi-episode Lawbook compounding evaluation`
5. `Add real SAIR artifact pack runner`

Keyword proxy scores:

- rank 1 scheduler / priority: **0 hits**;
- rank 2 operator construction: **0 hits**;
- rank 3 persistent multi-episode compounding: **4 hits**;
- rank 4 representation / continuation: **0 hits**;
- rank 5 verification / promotion hardening: **1 hit**.

### Semantic audit

This is a clean directional win for **version-space preservation over premature single-story collapse** at this checkpoint. The highest-ranked single story was wrong in the short horizon. A lower-ranked live rival, persistent multi-episode compounding, matches the revealed history directly and repeatedly, including the first revealed commit and the explicit multi-episode evaluation.

The result does **not** show that the precommitted highest-information separator would necessarily have caused the historical sequence, nor that the rank ordering was optimal. It does show that retaining rival developmental explanations prevented the controller from losing the actual near-term regime change.

## Controller update

Replace:

`JOIN -> one latent obstruction -> invent`

with:

`JOIN -> ranked developmental version space -> active separator -> shrink/re-rank -> invent late`.

Promotion rule: do not collapse to one developmental story while multiple rivals remain consistent with the residual field and a cheap separator exists.
