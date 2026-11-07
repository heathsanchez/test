# Nucleus: LOGOS-inspired scope-support census (CANDIDATE, diagnostic only)

Source authority: unchanged selected Nucleus archive from commit
`018135224632f72ba06a2818132c3e857d67eaad`, SHA-256
`cf0f4d6699c515d81d887242c1ae44d36c5e59ed826b091d6b92f09d61439755`
for its enclosing `nucleus_closed_lambda_and_capture_20261107.zip`.

Test authority: unchanged original `fueled-chain` prefix `chain9.ndjson`, SHA-256
`78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3`;
recorded `combined-work.stderr` observer from the preceding bounded experiment.
No Nucleus verdict or resource budget was modified by this census.

Run `python3 -m unittest discover -s experiments/nucleus-logos-support-20261108 -p 'test_*.py' -v`.
Then run `python3 experiments/nucleus-logos-support-20261108/support_census.py chain9.ndjson combined-work.stderr --top 30` using the two exact archived inputs.

Among the **30 most frequently observed expressions**, 292,298 summed calls
split by exact loose de Bruijn support: 175,955 have zero loose variables,
114,330 have one, and 2,013 have two. Important open applications:

| Expression | Calls | Inclusive charged steps | Exact source support |
|---|---:|---:|---|
| 2157 | 12,199 | 47,011 | [1] |
| 2339 | 9,015 | 28,803 | [2] |
| 2156 | 8,693 | 26,103 | [1] |
| 2158 | 5,252 | 36,418 | [1] |
| 4770 | 8,360 | 25,078 | [0] |

This does **not** establish that the calls share their captured values,
source-checked binder origins, expected types, universe instances, or cache
epoch. Nor are inclusive step totals savings estimates. It establishes only
which particular binding positions a later *typed* reuse experiment must
revalidate. The existing `closed_spine_eligible` optimization and previous
prefix-weakening, frame-interning, and result-alias candidates are distinct
negative controls, not claimed solutions.

## Next decisive experiment

Instrument an immutable per-typing-owner key `(expression, live source binder
node IDs, source-checked binder types, universe instance, policy, revocation
epoch)` for those one-variable expressions. Count repeated **complete and
protected** keys across distinct full-frame IDs without affecting any verdict.
Only if a substantial fraction repeats, test a bounded memo holding completed
types whose result does not capture unrelated binder frames. Preserve changed
source origin, changed domain, changed universe, malformed proof, and invalid
corpus controls. A template that requires FreeId coincidence alone is unsafe.

Independent residual: LOGOS's generic inductive-recursor derivation is an
architectural advantage over Nucleus's special-case admissibility branches.
Magma has local conversion/recursor gaps; complete Mathlib has a separate
structural-inductive frontier. Neither is discharged by this syntax census.

Status: `CANDIDATE` for further diagnosis; **no six original UNKNOWNs closed**.
