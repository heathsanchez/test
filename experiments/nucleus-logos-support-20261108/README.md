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

The first C4 source attempt [run #42430878438](https://github.com/heathsanchez/test/actions/runs/42430878438)
was `REJECTED` at compile time: besides the two public constructors, the
checker has three diagnostic-isolation constructors which also require unique
observation-lifetime IDs. The correction assigns fresh identities to all
five constructors, including nested diagnostic probes, and uses checked
atomic increment so ID exhaustion disables observation. No native outcome
was obtained from the failed build.

## C4b qualified; C5 checks result-binding provenance

[C4b run #42431001191](https://github.com/heathsanchez/test/actions/runs/42431001191)
is **SUCCESS**; artifact `13597428263`, ZIP SHA-256
`6573600bea6d6b6ee2dc75499f393a836a29b44de6fbd6422624930d0dd0afe5`.
The original 403 verdicts matched identically (240 ACCEPT, 150 REJECT,
13 UNKNOWN); all six unchanged originals remain UNKNOWN at 262,144 steps.
Original `app-lam` ACCEPTed independently with selected, observer-OFF and
observer-ON binaries. With lifetime-distinct checker IDs, all **762**
cross-frame projected-key disagreements persisted within the same checker.
Every resulting type expression was syntactically **open**: 0 closed,
762 open, 0 support-unknown. This rules out empty-environment reclosure.

C5 measures the narrower source-qualified condition without returning a
cached value: for each open result expression, compute complete free de Bruijn
support (bounded by 4,096 traversal units, 16 indices, max index 512), then
compare the immutable `EnvFrame` node reached by *each used index* in the
previous and current closure. Equal nodes prove identical captured bindings
even where unused outer bindings differ; unequal or unavailable nodes are
never considered proven-equivalent. Synthetic controls test an unchanged
used binding, a changed used binding, and an out-of-range binding. The
diagnostic does not alter kernel inference, conversion, admission, resources,
or claims of full Mathlib acceptance. C5 is **CANDIDATE** pending native
qualification, not a fix for the remaining six UNKNOWNs.

## C5 completed; all 762 captured result supports match

[C5 run #42431647689](https://github.com/heathsanchez/test/actions/runs/42431647689)
is **SUCCESS** at commit `f82a77c796c78f2ebfe298801899a48406e87897`.
Artifact `13596809762` ZIP SHA-256
`d04dbdd95b58f7955c0a287447a2e8568b525743a0103d7f2ae9ac96429ab49d`.
Native tests passed. The original `app-lam` passed all three configurations.
All 403 protected verdicts matched (240 ACCEPT / 150 REJECT / 13 UNKNOWN).
All six original valid inputs remained UNKNOWN under the standard 262,144
step limit.

Of 762 cross-frame repeated projected keys, 762 current and previous results
have **identical immutable binding node identities at every used free index
of their result type expression**. All 762 results are syntactically open;
0 capture-support failures, 0 changed used nodes, 0 genuinely closed results.
Their whole captured `EnvFrame` identities nevertheless differ.
The precise **WARRANTED_BOUNDED** conclusion is therefore a missed semantic
equivalence opportunity in the *observed* results. It does not yet establish
predictive, independently verified reuse: the current result environment
cannot be inspected until after inference. C6 must test which of those 762
could be certified from a previously typed result and source-checked caller
frame *before* paying full inference. No claims of six-case completion or
source-qualified complete Mathlib are warranted.

## C6 pre-inference result capture availability (PENDING)

The C5 comparisons knew *both* type-result closure environments only after
running the expensive inference twice. C6 checks the predictive prerequisite
using only the **previous** completed result and the **current caller's input
frame**, available before a subsequent inference. For every proved-equal
pair of result support node IDs, count whether each previously used node
(a) is at the same de Bruijn position in the caller frame, (b) is somewhere
else in the caller frame, or (c) is absent from it. An unavailable prior
capture is separately unknown. Unit controls distinguish these categories.
Membership or index identity here is **not** a transport proof, only a way
to decide which safety condition can be cheaply checked before replay.
No typing or conversion result is returned by this diagnostic.

## C6 result: predictive caller-frame reuse rejected

[C6 run #42432164811](https://github.com/heathsanchez/test/actions/runs/42432164811)
is **SUCCESS**, artifact `13598391535`, ZIP SHA-256
`24d2731c7f6ce2fe299535072cec8576ac7d9840ea43d5994ee618f734ad7fb6`.
Native tests and unchanged protected 403/403 passed; the original `app-lam`
passed all three configurations; six unchanged valid originals remain UNKNOWN.
All 762 proved-equal result supports were **absent from the subsequent
inference caller's input frame**: zero same-index, zero present at another
index, 762 absent. This **REJECTS** the direct predictive prior-result memo
as a safe strategy; the next result capture context cannot be reconstructed
from the source caller's frame alone.

## C7: exploit same-node reflexivity inside existing conversion (CANDIDATE)

An alternative does not require predicting a future result: the already
existing `exact_source_capture_identity` equality checker has *both* input
closures. After its own complete paired-source support and exact universe
checks, C7 can recognize when the two expressions read the same immutable
binding node at every relevant index. This is a narrower case of the already
implemented capture-reflexivity proof, not a new recursor or untyped equality
axiom. A metered early node-identity check avoids repeatedly resolving the
same captured closure or local. Nonidentical, missing, exhausted, changed
source and changed universe cases still follow the original checker logic.
Diagnostics count the number of skipped redundant capture descents.

C7 is the first **active optimization candidate** in this research sequence.
It is not admissible for release unless native tests, unchanged protected
403-case vector, adversarial controls, six-original replay and stack
preflight independently qualify it. Even if those pass, any improvement
must be measured against unchanged source/budget; no independent complete
Mathlib acceptance is asserted.

## C7 qualification: authentic proof work skipped, but no closure

[C7 run #42432804224](https://github.com/heathsanchez/test/actions/runs/42432804224)
**SUCCESS**, artifact `13598137209`, ZIP SHA-256
`135106eb7c8a25b3a20113bf9342562dcca88fa344a48d64221ac825d5d7b548`.
Native tests passed and the protected **403/403** verdict vector matched
240 ACCEPT, 150 REJECT, 13 UNKNOWN; all three `app-lam` controls ACCEPT.
The metered node-reflexivity branch skipped **66,095** source-capture descent
operations on the unchanged chain9 diagnostic prefix. No original six-case
verdict changed: **six UNKNOWNs remain** under 262,144 steps.
Within-run timings were 13.970 s pristine, 13.715 s candidate/observer OFF,
14.366 s candidate/observer ON. Earlier C6's separate runner timings were
12.734/12.821/13.111 s; cross-run noise prevents attributing a stable speedup.
This is `WARRANTED_BOUNDED` for guarded identity shortcuts and intact 403
verdicts, but **NOT PROMOTED** into the selected kernel: it did not discharge
a consequential original obligation or establish a controlled speedup.

New native diagnostic inspection of unchanged Magma originals identifies
two distinct residual classes. `magma-list-pair-n7` and `n21` fail top-level
application typing with `unresolved-qualified-recursor-heads` even while
more than 261,000 steps remain globally, so their immediate obstruction
is not simple exhaustion of the outer budget. The nested native replay also
reported `reduction-budget-exhausted` at a separate, depleted exposure-fuel
owner. `magma-list-deep-n21` retains an unresolved qualified recursor head
with exhausted **local** function-type budget; `magma-list-deep-n36` first
encounters `rigid-type-constructor-mismatch` with substantial global fuel.
No missing recursor equality or constructor may be invented from those
diagnostics. The next decisive experiment must discriminate a legitimate
source iota/major-constructor step from a rigid neutral whose equality needs
a separately checked dependent-context proof. Preserve C6/C7 negatives.

## C8 exact beta-frame retention capacity (REJECTED AS CLOSURE)

On unchanged `magma-list-pair-n7`, source-qualified diagnostics under the
same 24 flags show repeated `NUCLEUS_BETA_BINDING_CACHE:capacity` events.
The selected evaluator intentionally stops retaining *new* exact lambda/let
argument frames after 8,192 entries; completed replay keys can then lose
future matching allocation identities, even though an old retained entry
remains protected. C8 changed **only** that bounded capacity to 32,768,
updated its saturation controls, and tested whether better exact-source
hash-consing prevents the nested recursor major from exhausting its own
shared exposure work owner. It neither assumes constructor iota nor changes
recursor qualification, inference rules, truth values or the standard
262,144-step limit. The C7 active capture shortcut is removed in C8 to
isolate this variable; C7 remains separately reproducible at its pinned SHA.

The existing `ExperimentalResumableExposure` flag was independently tried on
the four unchanged Magma inputs: **all four remained UNKNOWN** with the
same terminal reason categories. This is a separate negative result; merely
enabling another partial-prefix cache did not resolve the recursor residual.
Increased memory retention alone cannot warrant new typing/equality authority.

C8a [run #42433534691](https://github.com/heathsanchez/test/actions/runs/42433534691)
failed at Rust **test-target compilation only**, after the library compiled:
the two capacity-driven test loops inferred `usize` indices while `FreeId`
requires `u64`. There is no kernel verdict from C8a. C8b makes both test
loop indices explicitly `u64` with checked conversion; implementation and
fixed selected source are otherwise unchanged.

C8b [run #42433650321](https://github.com/heathsanchez/test/actions/runs/42433650321),
commit `bd8537cb30120321ef5235adf61a14fb043398b1`, artifact `13598407840`,
ZIP SHA256 `99531196e726a95d42bab72db417c79fd249a2a7cdb21b8bb32ad0b2f3ce0f96`:
native saturation and adversarial controls passed; **403/403 protected
verdicts preserved (240 ACCEPT / 150 REJECT / 13 UNKNOWN)**, unchanged
`app-lam` ACCEPT in all three preflights, unchanged chain9 UNKNOWN in all
three. **All six unchanged originals remain UNKNOWN** at standard budget;
in particular n7 stays UNKNOWN at 0.449 s. Replaying that exact C8b binary
with selected flags and diagnostic trace still reported 32 capped
`NUCLEUS_BETA_BINDING_CACHE:capacity` events and the same failure of a
qualified `Nat.rec` major when its nested work owner reached zero.
Therefore 32,768-entry retention is not a closure, and the candidate is
**NOT PROMOTED**. It does not prove unlimited retention would never help.

## C9 nested registered-major exposure (REJECTED AS CLOSURE)

The native `magma-list-pair-n7` trace was mapped against the original
`lean4export` name table: `NameId(147)=Decidable.rec`, `NameId(170)=Bool.rec`,
and `NameId(66)=Nat.rec`. The observed dependency is
`Decidable.rec -> Bool.rec -> Nat.rec`. The last fails while exposing its
captured major: `Unknown("reduction-budget-exhausted")`, with its **local**
shared owner at zero but more than 261,000 global typechecker steps left.
This is a candidate *operational* obstruction, not evidence that any
constructor or equality should be presumed.

C9 changes exactly one operational parameter: both branches of the same
registered-recursor major-probe site increase the per-exposure cap from
512 to 2,048, still bounded by the caller's same shared owner. The C8
retention-cap change and the C7 active source-capture shortcut are both
absent. The native red test `probe_c9_n7.py` checks byte-exact original
n7, all 24 selected flags, 262,144 overall steps and requires exit 0;
the unchanged C8b candidate fails it with exit 2 (observed RED).
Only if native C9 succeeds would the original 403-case protected replay
run; its fail-closed harness permits **UNKNOWN -> ACCEPT solely for the six
known-valid original inputs**, never changes to any other verdict and never
changes an original ACCEPT or REJECT. Test-only protocol changes cannot
grant kernel authority.

C9 [run #42434289455](https://github.com/heathsanchez/test/actions/runs/42434289455),
commit `90d50a4d13d76ea62332fe7101cd05f94d5243e5`, artifact `13599016567`,
ZIP SHA256 `178b202b3e402e0abbc36fb3fa7c2ed66cff5b97aaaea5ddf660b0122eedf692`:
Rust build and native proof/adversarial controls succeeded. The byte-exact
original n7 remained UNKNOWN (`exit 2`, 0.435 s); the deliberate red-green
gate failed and stopped before the expensive protected 403 regression.
Hence there is **no C9 403 qualification** and no new ACCEPT. Running the
resulting binary with selected flags and diagnostic tracing again showed
`Nat.rec` major `Unknown("reduction-budget-exhausted")` and local fuel zero.
Crucially, one logged **start** of registered `Nat.rec` had a caller-owned
allowance of 504, already below the previous 512 per-major ceiling;
the trace did not establish that this was the **terminal failing call**.
C11 subsequently identified a different terminal event with a fresh
124-step owner. The C8b and C9 major-start/work traces were identical.
Raising the inner ceiling cannot enlarge the observed 504-step call grant;
it also did not cure the unchanged test. C9 is a **REJECTED**
hypothesis, NOT PROMOTED; next inspect the conversion-side grant/ownership
and exact work already charged, rather than increasing another nested cap.

## C10 conversion-side budget route (WARRANTED BOUNDED DIAGNOSTIC)

Source audit found two independent calls in `convert.rs`: a certified Bool
constructor may request a full checked nested-recursor replay, but the
fallback `qualified_one_step_recursor_result` divides each available
comparison allowance by two **before** attempting the source registered
recursor. That loop currently attempts all nonempty constant applications,
including those that do not have qualified recursor metadata, and still
reserves half their available allowance. An observed Nat.rec start grant
of 504 is numerically consistent with half an outer 1008 allowance, but
the precise **terminal** native caller remains to be measured before intervention.

C10 restores the original 512 per-major cap, the original 8192 exact-frame
interner, and every selected inference/conversion rule. It adds only
diagnostic-gated descriptions of the *actual existing calls* to checked
recursor replay: which side, source head, qualified metadata, outer budget,
allocated probe, unused reserve and whether native replay proved a value.
The diagnostic runs only with `NUCLEUS_TRACE_REPLAY_CACHE=1` on the
byte-exact original n7. Test `probe_c10_route.py` was first observed RED
on unchanged C9 binary: original still UNKNOWN, but zero route markers.
If it turns green, protected 403 and all six byte-exact verdicts are
replayed at the selected 24 flags. No trace can grant a new typing or
equality result. The next change, if any, must be determined from this
source-qualified caller work trace rather than guessed budget increases.

C10 [run #42434810378](https://github.com/heathsanchez/test/actions/runs/42434810378),
commit `9a23db847c387ec04c46a5c12353093946c95f93`, artifact `13599421657`,
ZIP SHA256 `f76b85d0bd5d9901a095795e4bf0f342ec9e74d852e20f62f09f264e5f6597bd`:
native suite/adversarial tests, original chain9 three-way UNKNOWN, original
app-lam three-way ACCEPT and **403/403 selected protected verdicts**
(240 ACCEPT / 150 REJECT / 13 UNKNOWN) passed. All six originals still
UNKNOWN at standard budget. Diagnostic-only n7 logged seven conversion
probe routes under its exact SHA256:

* An unqualified `NameId(64)` constant was nevertheless probed at
  comparison budget 498; 249 steps were **reserved** for the failed
  one-step attempt (`qualified=false`). The log does not establish that
  249 actual machine steps were consumed; reservation is the confirmed
  inefficiency.
* Registered `Decidable.rec` at budget 503 was first attempted via the
  certified Bool-constructor route and then given a one-step grant of 251,
  twice; neither attempt proved a replay value.
* The same registered recursor at comparison budget 260,755 later
  received a one-step grant of 130,377; replay still failed. Thus the
  full source-qualified caller allowance by itself does not establish
  a constructor, and inner owner accounting must be examined.

The older replay-major diagnostic printed only the first 32 starts.
One *observed* `Nat.rec` major start had allowance 504, and a distinct
terminal failure printed local fuel zero; **do not infer they were the
same call without an uncapped failure-event grant trace**. C10 warrants
the conversion budget-allocation observation, but cannot yet identify
the actual terminal owner's provenance. A C11 diagnostic should record
the entry work grant at the precise failing `Nat.rec` event, plus its
source branch, before modifying the budget scheduler.

## C11 exact terminal recursor owner's provenance (QUALIFIED DIAGNOSTIC)

C11 extends only existing `TraceNestedRecursorIotaFailure` output at the
two actual failure sites in `Machine::qualified_recursor_result`: record
`stage=major|rhs`, the `entry_budget` from this call, whether an older
work owner existed at entry (`owner_on_entry`), and, for a failed major,
the byte-source major expression and captured frame identity. It does
not alter replay, fuel debiting, iota qualification or acceptance.

The existing original n7 trace test now has an optional
`--require-owner-event` assertion; it was first observed RED against
the actual C10 binary because old failure events lack the owner's entry
grant. The new branch must first make that exact test GREEN without
changing the original UNKNOWN verdict, then pass all native/protected
403 and adversarial/stack controls. Only the precise terminal owner
trace can identify whether the failure came from an RHS exposure
cap, major exposure cap, independent conversion owner or actual work.

C11 [run #42435284307](https://github.com/heathsanchez/test/actions/runs/42435284307),
commit `3e63826fde9b03b2795a01c7db79180840edceb6`, artifact `13598789887`,
ZIP SHA256 `8ebe0fa4a9970bcab0af5ed1e4256a6c1b8a04e63df6413bc836c8db49f3b259`:
native and adversarial tests passed, original `app-lam` all three ACCEPT,
**403/403 protected verdicts matched** (240 ACCEPT, 150 REJECT, 13 UNKNOWN),
and all six original valid inputs remained UNKNOWN under standard budget.
On byte-exact original Magma n7, the actual recorded failure event was:

```
NUCLEUS_NESTED_REPLAY_FAILURE:stage=major:depth=0:head=NameId(66):entry_budget=124:owner_on_entry=None:major_expr=ExprId(11):major_env=49566:major=Unknown { residual: ResidualId("reduction-budget-exhausted") }:fuel=Some(0)
```

`NameId(66)` is source-qualified `Nat.rec`; its entry owns a **fresh 124-step
allowance**. Thus 504 referred to a *different logged start*, not to the
terminal observed failure. Direct local replay of the exact C11 compiled
binary confirmed this failure with **only** the nested-failure diagnostic
enabled; the replay-cache trace is not required to cause that observation.
The event may still be a recoverable failed alternative in the overall proof
conversion, rather than the unique final proof obstruction. It must not be
promoted to a causal diagnosis without locating the caller and checking its
role in the result.

## C12 caller provenance with source-line evidence (CANDIDATE)

Three qualified-recursor entry points gain Rust `#[track_caller]`; only the
existing diagnostics-gated **failed-replay trace** prints the caller's source
file/line and `completed` versus `one-step` goal. This does not adjust the
work allowance, constructor witness, reduction, cache or verdict. The
red-green test `probe_c10_route.py --require-owner-event --require-caller-event`
was **RED** against the actual C11 compiled binary: unchanged n7 rc2,
one owner event, zero caller events. `c12-caller-site.patch` applies with
zero fuzz atop the exact C11 patch in a staged native build. The immediate
question is whether the 124-step Nat.rec failure originated in same-head
conversion's half-budget attempt, projection replay, or a separate caller;
do not allocate more steps or infer a missing constructor in advance.

C12 [run #42436047149](https://github.com/heathsanchez/test/actions/runs/42436047149)
**SUCCESS**, commit `1ba04a3c9543275cc7ed0e701132cefc784c0913`,
artifact `13599332984`, ZIP SHA256
`36393d0bc4dd2887cef9476d59a2bb947736d1046d7dbc104bfd6e0b8f068d2f`:
native/adversarial tests and the C12 red-green caller assertion passed;
all **403/403** protected verdicts matched 240 ACCEPT / 150 REJECT /
13 UNKNOWN, original `app-lam` three-way ACCEPT, and **all six** original
valid inputs remain UNKNOWN at 262,144 steps. The exact original n7
failure entry states:

```
head=NameId(66):entry_budget=124:owner_on_entry=None:caller=src/convert.rs:1862:30:replay_goal=one-step
```

This is the **same-head conversion fallback's speculative one-step
replay**, with its own half-budget grant. It cannot be equated with the
terminal unsolved equality. The final main comparison, independently
observed with `TraceNeutralHeads`, instead has source `Bool.true`
(`NameId(169)`) on one side and a five-argument source-qualified
`Decidable.rec` (`NameId(147)`) on the other, including a 260,755-step
comparison allowance. The native `TraceDecidableMajorChain` diagnostic
follows 41 consecutive same-recursor major layers and then a five-argument
`Bool.rec` (`NameId(170)`), whose major exposes to `Bool.true`. That
diagnostic gives each step its own up-to-256-step exposure, not a single
metered certificate, so it **does not prove** that the complete large-budget
replay succeeds or that the 41-layer path can be collapsed safely.

## C13 full-budget replay residual (CANDIDATE)

The next smallest decisive test is to log the exact `Judgment` residual of
the **large-budget certified Bool-vs-Decidable comparison**, and, if its
source-qualified recursor replay reaches the registered-rule test, the
actual exposed nonconstructor or unmatched constructor name/arity.
Existing `TraceReplayCache` and `TraceNestedRecursorIotaFailure` remain
diagnostic-only. The C13 protocol must first fail against C12's exact
binary, then pass unchanged input/native/adversarial/403 controls. No
recursor certificate or desired Bool constructor may be inferred from the
trace. This replaces the C11 local Nat.rec side-probe hypothesis, while
preserving C11/C12 as negative causal-lineage evidence.

C13 [run #42436611602](https://github.com/heathsanchez/test/actions/runs/42436611602)
**SUCCESS**, commit `2313b6b662766538b1b9c07e7c0f8b392c2378db`,
artifact `13600380201`, ZIP SHA256
`4675382817ad54d6220db4618988fc8f207a96ae8951f19495a98b9f8d1eb881`.
Native/adversarial and **403/403** protected passed; original `app-lam`
accepted all three ways; all six original valid inputs remain UNKNOWN.
The source-qualified large-budget **completed** replay returned
`projection-major-replay-budget` with a 260,755-step caller grant;
the subsequent one-step replay with grant 130,377 returned the **same**
residual. Smaller attempts (503 and 251 grants) also returned it.
This disproves the hypothesis that only the earlier 124-step speculative
`Nat.rec` probe caused failure. The real independent task is to determine
which *actual source value* was still being resolved when the shared
major-projection work owner depleted; neither increased top-level fuel
nor a presumed Bool constructor is warranted.

C13's additional diagnostic records many other `Nat.rec` attempts on
free local major variables, which safely remain UNKNOWN even though their
shared owners retain work. The `Nat.rec` 124 event remains a distinct
speculative failure; it is not the 260,755-step `Decidable.rec` residual.

## C14 exhausted major source shape (CANDIDATE)

At the existing `projection-major-replay-budget` return site, record
`step`, current source result shape, recursor head, root caller and
entry budget only under `TraceNestedRecursorIotaFailure`. The read-only
probe must determine whether the owner ran dry **before inspecting an
already-available constructor**, during a pending source projection,
or while carrying another qualified recursor. Distinguish these cases
before moving even an operational debit. The exact C13 native binary
was first tested RED against
`probe_c10_route.py --require-projection-major-boundary` while returning
unchanged n7 UNKNOWN. The new `c14-projection-major-boundary.patch` applies
with zero fuzz on the fully pinned C13 source. It never grants a judgment.

C14 [run #42437062148](https://github.com/heathsanchez/test/actions/runs/42437062148)
**SUCCESS**, commit `52661464ca9bcdb0b19b7fd88f31f00cc8974339`,
artifact `13599634775`, ZIP SHA256
`5865815507eaa9e232cb5b5415b8096c291ed4acb0289e961811b8ba5e33aefe`.
Native/adversarial tests passed; all 403/403 protected source outcomes matched
240 ACCEPT, 150 REJECT, 13 UNKNOWN, including original `app-lam`
three-way ACCEPT. All six unchanged valid original cases remain UNKNOWN at
262,144 steps. The actual source-qualified large-budget `Decidable.rec`
failure now identifies its exhausted value:

```
head=NameId(147):entry_budget=260755:caller=src/convert.rs:2046:54:
replay_goal=completed:depth=2:step=1:owner_on_entry=None:
major=neutral=Const { name: NameId(147), levels: [Succ(Zero)] }:
arity=5:qualified=true:fuel=Some(0)
```

The 130,377-step one-step attempt fails the same way. This is not evidence
of an ineligible four-argument Bool recursor or an invented constructor.
**The projection resolver returned a source-qualified five-argument
Decidable recursor, but had drained the common work owner before the
qualified recursor worklist could continue.** C14 is WARRANTED_BOUNDED as
diagnostic evidence only; the actual source proof remains UNKNOWN.

## C15 finite speculative projection grant (CANDIDATE)

The single operational source change caps only the *speculative*
`projection_value_for_conversion` trial **inside an existing qualified
recursor major worklist** at 512 of the owner's remaining steps, without
creating new work. The same source constructor, rule checks, original
captures, shared owner and result-verdict logic remain authoritative.
This is analogous in purpose, not in implementation, to nano-lean v0.3.2's
targeted cost reductions for deep List reductions (exact commit
`54ce971a5ac2513a1bac0ac9bca73f672196c0f2`, 5 November).
Nano-lean's independent `mk_pi` interning and `inst_pi` exact
codomain memo are separate ideas, not yet imported or validated here.

Native `probe_c10_route.py --allow-accepted --require-bounded-projection`
returned **RED** on the actual C14 release binary, unchanged n7 UNKNOWN:
no C15 bounded-projection event. The C15 source patch applies with zero
fuzz to C14's exact source. The next GitHub run must show this event
GREEN, original n7 verdict, all native/adversarial tests and 403 protected
results. The 403 qualifier permits UNKNOWN to upgrade only for the six
byte-hash-frozen independently valid inputs; all other changes fail closed.
Until that run qualifies, **C15 has proved no acceptance or soundness result**.

C15 [run #42437592021](https://github.com/heathsanchez/test/actions/runs/42437592021)
**SUCCESS**, commit `43eff6619a37a4d2f94f6979b7821d4149abeb0b`,
artifact `13600118180`, ZIP SHA256
`c8c6c89a45e2448e8b30039cb77c34fca77be1277dbad02f0f25844dac175aed`.
Native/adversarial passed, 403/403 protected matched 240 ACCEPT / 150 REJECT /
13 UNKNOWN, exact `app-lam` three-way ACCEPT. All six original valid cases
remain UNKNOWN. The *large-budget completed* Magma n7 replay changed from
C14 `projection-major-replay-budget` at worklist depth 2 to
`nested-recursor-iota-budget` after additional source-qualified worklist
continuations; the separate 130,377-step one-step attempt reached depth
**54** before owner exhaustion. This is genuine deeper diagnostic progress
but **zero new original ACCEPTs**. C15 does not prove a true borrowed cap.

## C16 explicitly metered projection sub-owner (CANDIDATE)

Source review found a concrete gap in C15's assumption: passing a
`budget.min(512)` argument to `projection_value_for_conversion` is
**not sufficient** to constrain nested `qualified_nested_recursor_result`,
because an already-present `self.exposure_fuel` owner takes precedence.
C15's 512 parameter can therefore leave the original 260,755 owner exposed
to exhaustion. This is an implementation-level finding; C15's actual
native verdict must still be read from its separate run.

C16 wraps **only** the speculative projection field trial in the existing
`MeteredConversionWork` accounting scope: borrow up to 512 remaining
steps, temporarily set this as the nested owner, restore the old owner
on exit, and debit exactly the actually spent steps. No new work allowance,
constructor assumption, independent authority change, cache equivalence,
or verdict exception is introduced. A diagnostic
`NUCLEUS_PROJECTION_MAJOR_BORROWED` is the new red/green execution gate.
The original six and all 403 protected verdicts remain mandatory. If a
source projection needs over 512 steps to expose a real constructor, this
candidate may remain UNKNOWN; it may not invent a constructor.

C16 red/green prerequisite was confirmed **RED** on the exact C15 native
release binary (unchanged n7, rc=2, bounded-projection records present,
zero borrowed-owner events). C16's separate GitHub run must become GREEN
with the actual metered owner and pass all protected cases before it is
considered qualified. This prevents C15's shallow-argument marker from
being misinterpreted as actual nested fuel containment.

C16 [run #42437765990](https://github.com/heathsanchez/test/actions/runs/42437765990)
**SUCCESS**, commit `071d370c7a0a33bc151bcd1ea8ce2984e5f92541`,
artifact `13600078686`, ZIP SHA256
`d2118eb3147c8f115499647edc9a79085c306f16fb1411198ff73393b72e7829`.
Its original n7 source still returns UNKNOWN. Native/adversarial passed,
all 403/403 protected outcomes matched 240 ACCEPT / 150 REJECT / 13 UNKNOWN,
and **none of the six valid original inputs upgraded**. A source-qualified
completed Decidable replay under the full 260755 comparison allowance
reached depth **66** before `projection-major-replay-budget`, and its 130377
one-step alternative reached depth **52**. The trace proves a real borrowed
projection owner at 512 with parent grants 260632, 260084 and 259536,
charged across successive nested recursors. C15's one-step reached depth
54 with no actual sub-owner cap; neither demonstrates monotone progress
to constructor or a full proof. C16 is WARRANTED_BOUNDED as a checked,
regression-qualified *operational* implementation, **not promoted** to
Nucleus's selected kernel because the original six still fail.

The remaining decisive question is whether 512 is a badly chosen local
bound or whether this source chain fundamentally needs a resumable
projection/recursor continuation or exact source-derived rule sharing.
Evaluate several honest local grants under the same **global** 262144 owner,
using the identical original n7, before altering proof semantics or
building a complex cache.

## C17 source-pinned borrowed-grant sweep (CANDIDATE)

One diagnostics-only setting `NUCLEUS_DIAGNOSTIC_PROJECTION_GRANT` selects
a finite borrowed grant in the range 48..8192, preserving the independent
registered recursor/projection checks, the single shared 262144-step owner,
and default 512 when unset. Invalid or non-Unicode values yield UNKNOWN.
The sweep evaluates 64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048,
4096 and 8192 against the same exact original Magma n7 SHA256
`abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`,
plus one malformed-cap control. Every trial must be ACCEPT or UNKNOWN,
never REJECT, timeout, or uncharged larger grant. The ordinary 403 protected
suite still runs with the unmodified 24 selected flags and default 512.
No cap-specific ACCEPT would qualify for release before a separate full
403 native/adversarial run with that exact frozen cap.

The exact C16 native release binary was tested **RED** on the C17 sweep:
it ignores the new grant setting and still logs 512 even when asked for 64.
The C17 diagnostic source patch applies with zero fuzz over C16. A run
passing the sweep would establish actual parameter sensitivity only; this
experiment seeks an original unchanged ACCEPT or a reason to reject grant
tuning and move to deferred projection/reduction rule sharing.
