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

## Native source-qualified observation, 8 November (negative evidence)

[GitHub Actions run #42427937639](https://github.com/heathsanchez/test/actions/runs/42427937639)
restored artifact `13520537513` (ZIP SHA-256
`f8dc913015842af9a923c6b419f29d9b2fad14e269ea8bfbbbbcce9ffd7a9b0f`,
selected source tarball SHA-256
`f1614835294c40a206f58accf9835ceeaae646eedb5cd4bebfac1d7c85d89ae4`).
Rust compilation and native tests passed; pristine, observer-OFF and observer-ON
all returned UNKNOWN for the unchanged chain9 prefix SHA-256
`78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3`.

The observer recorded 35,181 complete hot-expression source typing results;
20,000 unique keys were retained and 14,419 insertions were declined at the
fixed capacity. Under *complete checked node support plus identical full
TypeValue context and captured flags/epoch*, 762 cross-frame key repetitions
returned **different TypeValue representations** and zero returned identical
representations. This falsifies the simple proposition that a projected
support key can be used to return a previously inferred TypeValue verbatim.
No result was added to the kernel's typing memo. Classification of the 762
differences is the next decisive experiment; a canonical/reclosed type result
would itself need a proved transport boundary, not an assumption.

The first patch had a genuine implementation regression: on the identical
`app-lam` source SHA-256
`552d6e8398f579fcf59ab9abd8187fc7a8a037697da66c129aacb4cc1b9dd414`,
the pristine selected binary ACCEPTed but the observer-enabled *build* aborted
with `stack overflow` even when its trace toggle was OFF. Both copies of that
input in the 403-case corpus reproduced the failure; the other 401 outcomes
were unchanged. This was not a forged ACCEPT. The V2 patch moves its large
diagnostic key construction to a `#[cold] #[inline(never)]` method and adds a
single-case observer-OFF/ON stack preflight before any broad replay. Until
that native replay passes, V2 is a **CANDIDATE**, not a regression-qualified
repair. The first trial remains `REJECTED` for release use.

## V2 result and C3 stack-frame experiment, 8 November

[Run #42429803743](https://github.com/heathsanchez/test/actions/runs/42429803743)
compiled, passed native tests and restored both pinned corpora. All three
chain9 verdicts stayed UNKNOWN. The new source-qualified observer counted
**762/762** cross-frame differences in which both result closures had the
**same source expression and identical level substitution**, and only their
captured `EnvFrame` identity differed. No `Sort`, `Pi`, expression or universe
variation contributed to those 762. This makes **checked, source-relative
reclosure** the narrowest interesting typed-reuse hypothesis. It is not a
proof that these closures are interchangeable, and no verdict was promoted.

The V2 candidate still aborted `app-lam` with the observer **OFF**, so it
remains `REJECTED` as a full protected build. Native ELF disassembly identifies
the compilation mechanism: the selected build's `infer_in` used one 0x508-byte
stack frame with `infer_uncached` inlined, whereas V2 compiled `infer_in`
(0x348) and `infer_uncached` (0x508) as separate mutually recursive frames.
The relevant thread config explicitly fixes a 64 MiB stack, so changing the
environment's `RUST_MIN_STACK` cannot repair this case. C3 tests an
`#[inline(always)]` hint on `infer_uncached` with **unchanged source proofs,
canonical flags and 403-case verdict comparison**. If this still fails, it
must not be used for the selected kernel. Neither run closed any of the six
original unchanged UNKNOWN exports under the standard budget.

## C3 qualified and C4 provenance/closure audit, 8 November

<https://github.com/heathsanchez/test/actions/runs/42430277247> is **SUCCESS**
with observer artifact `13596963984`, ZIP SHA-256
`b8750d7b04407de8dd981976e1763a9ecbb1b48a6e488adb284e4d528bc0afd3`.
Its restored input source, standard 262,144 budget and 24 flags match the
selected source. Native tests passed. `app-lam` independently ACCEPTed in
pristine, observer OFF and observer ON. The full 403-case comparison matched
the selected verdict vector exactly: **240 ACCEPT, 150 REJECT, 13 UNKNOWN**.
All six unchanged originals remain UNKNOWN. The earlier stack-overflow
regression is fixed in this *diagnostic build* by explicitly inlining
`infer_uncached` again; neither the observer nor that optimization changes
typing authority. No Arena/main implementation was selected or submitted.

C3 retains the exact result-shape observation of 762 differences solely in
captured type-result environments. However an additional provenance flaw in
the *measurement key* remains: `self as *const Self as usize` is not a unique
TypeChecker lifetime. Successive declarations can reuse the same address.
The 762 cannot be promoted to within-owner reusable work without excluding
this alias. C4 assigns each fresh checker instance a non-repeating diagnostic
identifier, fails the observer closed if that ID space is exhausted, and
rechecks its measured cross-frame coincidences. It additionally measures
whether the **result type expression itself** has empty complete de Bruijn
support. A closed result would make source-relative reclosure worth testing;
an open or unsupported result must not be silently rewritten to empty Γ.
No C4 observation has returned yet. C3 is `WARRANTED_BOUNDED` only for
non-mutating observer qualification and its reported representation classes;
actual cross-owner transport and six-case closure remain `UNKNOWN`.
