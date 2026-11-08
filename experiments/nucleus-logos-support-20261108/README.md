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

C17 [run #42438356021](https://github.com/heathsanchez/test/actions/runs/42438356021)
**SUCCESS**, commit `82af813771e4c0b32a1e29db36ef2a53944c1da2`,
artifact `13600443617`, ZIP SHA256
`614cd55f324a2adc9dfc1f15194584dbe0dfe5b2f348e4df5e9b03572e1bd523`.
The actual source-pinned diagnostic grants **64, 96, 128, 192, 256, 384,
512, 768, 1024, 2048, 4096, and 8192** all returned original n7
`UNKNOWN` (exit 2), with no ACCEPTs or REJECTs. Borrowed-owner logs show
real sensitivity; maximum exhausted worklist depths by cap were respectively
`0, 4, 2, 4, 2, 2, 66, 64, 2, 68, 2, 36`—neither monotone nor a
constructor witness. The malformed grant failed closed as UNKNOWN. Native
and adversarial checks passed; the 403/403 independently protected cases
still matched **240 ACCEPT / 150 REJECT / 13 UNKNOWN**, and all six
original valid residuals stayed UNKNOWN. C17 is WARRANTED_BOUNDED as a
diagnostic **negative result**: scalar projection grant tuning in this
range cannot close n7 under the standard global 262144-step allowance.
No grant-tuned kernel is promoted, and neither complete Mathlib nor six-case
closure is claimed. The next experiment must test *structural sharing or
resumption of source-certified work*, not another cap sweep.

## C18 checked projection continuation (CANDIDATE, UNQUALIFIED)

A replay of the unmodified original n7 with the C17 native binary and the
same 24 flags produced **462 actual recursor-major captures** (`NameId(66)`
305, `NameId(147)` 106, `NameId(170)` 51), with only one logged completed
replay hit. This is evidence of repeated checked recursor work; it does
**not** prove equivalent captured environments or authorize generalized
memoization. The current field-probe recursively invokes its own recursor
evaluator even when the caller already holds a checked recursor worklist.

C18 tests exactly one alternative: when a stuck source projection's actual
receiver exposes a *registered recursor*, suspend its source projection
and check that receiver using the existing worklist and global fuel owner.
Only after the receiver produces the *actual checked source constructor*
may C18 match its registered projection type, constructor and exact arity,
select its independently registered field, apply the original pending
spine, and resume the parent. If any step cannot be source-confirmed,
return UNKNOWN. Other projections take the old C16 metered fallback.
No constructor is inferred from expected Bool, no new rewrite authority,
and no budget increase is permitted.

Native `probe_c18_projection_worklist.py` was run against the exact C17
release binary: **RED**, original n7 UNKNOWN, zero deferred-projection
events and seven projection-major exhaustions. The C18 source diff applies
with **zero fuzz** to the C17 source. The GitHub candidate must first
compile, become GREEN on its new `NUCLEUS_PROJECTION_MAJOR_WORKLIST_DEFERRED`
event, and pass all native/adversarial plus 403/403 source-frozen protected
outcomes before any bounded progress is claimed. The six valid original
cases must become ACCEPT under 262144 for the primary objective; otherwise
C18 is not a completed Nucleus kernel.

C18 [run #42439294535](https://github.com/heathsanchez/test/actions/runs/42439294535)
**SUCCESS**, commit `039c9eb71e5467d8e1ceb79ff9a0a46ebf77f1c4`,
artifact `13600634247`, ZIP SHA256
`78c258052e897b81fa3c2b21fc6804ec51c16ab9a86626207d775823bc230cae`.
The original frozen n7 remains **UNKNOWN**, but the source-checked
projection continuation executed (32 diagnostic records, capped for output)
and projection-major exhaustion traces dropped from 7 to 1. All native and
adversarial tests and the independently protected **403/403** suite passed
with precisely **240 ACCEPT / 150 REJECT / 13 UNKNOWN**. All six unchanged
valid originals remain UNKNOWN; Mathlib completion remains unproved.

An additional identical-input, diagnostic-enabled C18 replay observed **622
worklist recursor-major captures** (`Nat.rec` NameId66: 544;
`Decidable.rec` NameId147: 64; `Bool.rec` NameId170: 14), versus 462
in C17 (Nat:305, Decidable:106, Bool:51). C18's completed Bool comparison
attempt failed with `nested-replay-key-work`, and its one-step alternative
with `nested-recursor-iota-budget`. The lower n7 wall time (0.255 s versus
0.47 s) reflects a different early UNKNOWN path, **not proof-efficiency or
semantic-completeness improvement**. Therefore C18 is WARRANTED_BOUNDED
only as source-checked control-flow implementation, but its proposed
route to n7 acceptance is **REJECTED**; do not promote it into the selected
kernel. The new bottleneck is worklist expansion on environment-dependent
`Nat.rec` major subcomputations, including free/stuck majors. Any new
sharing must retain binder/capture origin and never equate different
environment frames merely because their syntax looks similar.

## C19 pinned nano-lean differential reference (CANDIDATE, ADVISORY ONLY)

The next least-assumptive architecture check uses the actual upstream
`sdiehl/nano-lean` v0.3.2 commit
`54ce971a5ac2513a1bac0ac9bca73f672196c0f2` in a **separate binary**,
against the six SHA256-frozen original valid exports and four SHA256-frozen
forged controls. Its local harness has RED-first/green tests for immutable
input digests and for refusing to treat exit-zero as a Nucleus warrant.
No Nucleus implementation, selected flags, standard kernel work budget or
protected verdict is changed. Its `--steps=262144` units belong to the
external implementation and are **not** equal to Nucleus work units.

Upstream's [trust-model documentation](https://github.com/sdiehl/nano-lean/blob/54ce971a5ac2513a1bac0ac9bca73f672196c0f2/docs/TRUST.md)
explicitly requires a trusted reference prelude to prevent an attacker
from redefining certain primitive bodies under their existing types.
The C19 fixture replay does not supply such a source-qualified prelude;
thus even a reference checker `ACCEPT` is only an architectural observation,
not independently WARRANTED proof or permission to reuse its trust model.
If the reference accepts a forged test, fail the run and retain the
separating witness. If it accepts valid n7 within its own resource metric,
investigate **value-level interning, certified rule derivation and closure
support** as an architectural path, not as an unverified target-driven
shortcut. If the source format fails import, report a compatibility
obstruction without inferring proof failure.


C19 [run #42439880259](https://github.com/heathsanchez/test/actions/runs/42439880259)
**SUCCESS**, candidate workflow commit `a6ecd5b7b8d5f438919c4ae013a6ad1a7c42d9b9`,
artifact `13601481355`, ZIP SHA256
`8341d4e81bfd023c69a890fcb545df6aab2c995b4f130aef3259d5a20efd9b9c`.
All ten frozen source input hashes were verified. At nano-lean's own
`--steps 262144` limit, the untouched `fueled-chain` reference input
was `REFERENCE_ACCEPT_UNQUALIFIED` (200 declarations, ~31.6 ms), while
`grind-ring-5`, `magma-list-pair-n7`, `magma-list-pair-n21`,
`magma-list-deep-n21`, and `magma-list-deep-n36` were each
`REFERENCE_UNKNOWN` due to a declaration work budget exhaustion.
The four frozen forged controls
`nat-rec-k-lie`, `rec-missing-ih`, `nat-lit-add-bad`, and
`proj-of-stuck-prop` were `REFERENCE_REJECT_UNQUALIFIED`.
This does not qualify nano-lean as an independent source-sound checker:
the reference run omitted its required trusted prelude, and its step
unit is incomparable to Nucleus's 262144 work charges. Consequently
**zero Nucleus cases are promoted by C19**, all six unchanged original
valid cases remain UNKNOWN in Nucleus, and full Mathlib is still unproved.

C19 yields a decisive separation of residual families rather than an
external shortcut: the reference checker has a cheap route on
`fueled-chain` that Nucleus lacks, but it too exhausts all five
grind/Magma cases at the nominal limit. The earlier C5/C6 audits provide an important stronger negative
control: all 762 apparent type-result support matches were equivalent
only after both inferences had completed; none of their required
captured bindings was available from the *next inference caller frame*
ahead of time. Therefore direct predictive cross-frame type reuse is
**REJECTED**, including source-support-key weakening; do not rerun it.
Magma recursor and grind arithmetic work remain separate UNKNOWNs.

## C20 reference core-mode ablation (WARRANTED_BOUNDED differential)

The same exact nano-lean source and ten frozen exports now replay both
its default value checker and its distinct `--term-core` checker, with
the same external 262144-step setting, to determine whether the
reference's cheap `fueled-chain` acceptance depends on value-level
semantics (NbE, interned neutrals and Pi instantiation). This is a
causal-discriminator experiment, **not** a proposed source-soundness
substitution. A RED-first/GREEN local unit test confirms `--term-core`
is supplied only for the term ablation; source hash checks, explicit
unqualified verdict labels, and forged control failure gates remain.
The workflow modification at
[commit 6ceae9e](https://github.com/heathsanchez/test/commit/6ceae9e4851401cad1b0d8979c61853c682f0337)
[C20 run #42440338082](https://github.com/heathsanchez/test/actions/runs/42440338082)
is **SUCCESS** at workflow commit
`6ceae9e4851401cad1b0d8979c61853c682f0337`, artifact
`13601467155`, downloaded and SHA256-verified ZIP
`5e4cee34d5dd2d768f70338e59734e9ebc838f4cecf0e598ec565f63dba7837c`.
Both exact baseline-value and counterfactual term core compiled and completed
the identical ten SHA256-pinned original exports, same external
`--steps 262144` argument. On `fueled-chain`, default value-core
`REFERENCE_ACCEPT_UNQUALIFIED` (200 declarations, ~31.6 ms),
but term-core `REFERENCE_UNKNOWN` (four source declarations
`chain6_datF`, `chain9_datF`, `chain12`, `chain12_datF` exhausted
declaration work budgets, 200 declarations total). The other five original
valid cases were UNKNOWN in both modes. All four forged controls were
REJECT_UNQUALIFIED in both modes. The term-core result is not an unsafe
accept, and the lack of trusted prelude remains; neither is an independent
proof warrant.

**WARRANTED_BOUNDED conclusion**: the value-checking architecture materially
affects this exact case under nano-lean's own resource meter. This does
**not** isolate which value-core component is causal: NbE, value
interning, projection-aware inference, Pi codomain memoization,
guarded derivations, and scheduling all differ. It does **not** imply
that copying nano's checker or a single optimization would safely close
Nucleus. Prior Nucleus C5/C6 predictive cache transport was already
REJECTED; no source-unsafe frame quotient is now admissible.

Next cheapest decisive experiment should isolate *one* exact source
reference mechanism inside value core, e.g. instrumentation of
`NL_VSTATS` per-source declaration counters before considering a
single guarded Nucleus value-level operation. The full Nucleus
primary/secondary completion obligations remain unchanged: **six
original valid cases UNKNOWN at standard 262144, complete Mathlib
unproved**.



## C21–C22: pinned value-core counters and single-cache ablation, 8 November

C21 [run #42442557387](https://github.com/heathsanchez/test/actions/runs/42442557387), commit `68a0364af8e3e0daba33225049d9e6987419e2e3`, **workflow FAILURE** due to an erroneous reporting assertion that expected an aggregate `vstats total` line. The pinned reference actually prints **per-declaration** lines. Its recovered artifact `13601942430`, ZIP SHA-256 `8bfefc5076d10353a5fa83d2ccdbfe10e2a14b6432a3cdf20cbb9503ea1228a2`, shows the unmodified reference did ACCEPT the unchanged original `fueled-chain`; however, the failed workflow itself must not be promoted as a passing qualification. This gate was repaired in C22.

C22 [run #42442888328](https://github.com/heathsanchez/test/actions/runs/42442888328), commit `7b3fc102eb0e902661ad50543e2c7b302e630270`, **SUCCESS**, artifact `13602252775`, verified ZIP SHA-256 `25b0819dacec988f04b76a868264d16b7f377ee501798cc9ef80e42075e1f1ca`. The harness tests passed. It first built unmodified `sdiehl/nano-lean` at pinned commit `54ce971a5ac2513a1bac0ac9bca73f672196c0f2` with feature `vstats`, verified the unmodified source hash of the original `fueled-chain` export, and measured the reference's actual Pi-instantiation memo hits. Then it applied the tracked two-function-line change `c22-nano-no-inst-pi-memo.patch`, removing **only** the untyped `inst_pi` results-cache lookup and insertion, rebuilt, and reran the exact unchanged input at reference `--steps 262144`.

In the unmodified `chain12_datF` reference declaration, `inst_hit=42,844`, `memo_hits=81,228`, `applies=32,991`, and `closed_hit=42,255`. Under the isolated instantiation-memo ablation, `inst_hit=0`, `memo_hits=120,286`, `applies=76,083`, and `closed_hit=42,173`. Both runs **ACCEPTED** the complete unchanged `fueled-chain` with zero resource-exhausted declarations. These counters reveal increased internal work, but are not interchangeable with Nucleus's charged steps or wall-clock savings.

**REJECTED hypothesis:** the untyped Pi-instantiation memo, by itself, is necessary for nano's successful reference replay at this budget. **WARRANTED_BOUNDED:** it substantially reduces nano's counted work, yet its removal does not change this outcome. **UNKNOWN:** which remaining source-qualified value-level mechanism, if any, can safely close Nucleus's six original unchanged valid UNKNOWNs. The external reference's required trusted prelude was not supplied, and its checking authority does not transfer to Nucleus. The selected Nucleus implementation, standard budget, six valid residuals, protected forged-proof regressions and separate full-Mathlib claim are unchanged. The cheapest next controlled test is an isolated memoization ablation of a distinct dominant value-core counter, with the same frozen input and explicit trust boundary—not an implementation change to Nucleus based on correlation alone.


## C23 isolated closed-type memo ablation; false-positive gate repaired, 8 November

C23 [first run #42443269464](https://github.com/heathsanchez/test/actions/runs/42443269464), commit `e9075d86c85d8a95f4a2b24b8f029a54d5e3973a`, **FAILED reporting gate**, artifact `13602174182`, ZIP SHA256 `78ca51e3fe822be1621e94653c1caf78ea966ec308032154704903805e2f1c61`. The compiled, separately patched nano reference **ACCEPTED** the unchanged original `fueled-chain` with exit zero; all 113 native `vstats` declarations contained exact `closed_hit: 0`. But an ambiguous regular expression erroneously matched `mk_pi_closed_hit` as `closed_hit`. Preserve the failed workflow as an integrity-gate false positive, never reclassify it as overall SUCCESS.

The RED-first/GREEN local test `test_vstats_contract.py` (four tests) and exact-field parser `vstats_contract.py` now prohibit suffix confusion, duplicated/malformed counters, missing declarations, and missing counters. The full harness now passes 11/11 Python unit tests, up from 7. [C23 rerun #42443702567](https://github.com/heathsanchez/test/actions/runs/42443702567), commit `6172be84108dd3522cf8e62934ae627170ff6441`, **SUCCESS**, artifact `13602558434`, independently verified ZIP SHA256 `0263725f66bf680f0b36dc467a2f4e591abe8f9b75e8c54293f15163a45041dd`, reports `c23-fueled-chain.exit=0` and `c23-closed-hit-contract.json` selecting **113 declarations all with exactly zero closed inference cache hits**. Source remains exact pinned `sdiehl/nano-lean` at `54ce971a5ac2513a1bac0ac9bca73f672196c0f2` before the isolated `c23-nano-no-closed-type-memo.patch` (only three guarded cache lookups disabled). The C22 Pi memo patch is **reversed** before C23, ensuring an isolated intervention. The original `fueled-chain` SHA stays `e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a`.

In the successful run's `chain12_datF`: pristine `inst_hit=43,041, closed_hit=42,316, memo_hits=81,389`; C22 **Pi memo off** `inst_hit=0, closed_hit=42,183, memo_hits=120,727`; C23 **closed memo off** `inst_hit=88,248, closed_hit=0, memo_hits=110,588`. All three reference stages ACCEPT; the counters demonstrate compensatory activity but **not** equivalent work, proof authority or Nucleus steps. Therefore both individually-necessary hypotheses are **REJECTED** at this specific reference boundary; neither independently determines nano's ACCEPT. C24 completes the 2×2 interaction with both disabled, source frozen, by [run #42443995624](https://github.com/heathsanchez/test/actions/runs/42443995624) (PENDING at writing).

Cross-check against Nucleus's independent original `chain9` observer: 95,048 calls to syntactically closed `App` expressions; 95,001 already fall within its guarded closed-spine grammar; only 47 calls fall outside. This is a **source-census**, not a measured 95,001 cache hits; it undercuts the claim that broadening Nucleus's closed-expression grammar alone is a likely solution. The external reference's omitted trusted prelude and noncomparable step meter still prohibit promotion to a Nucleus proof. The six original Nucleus UNKNOWNs and full Mathlib residual remain OPEN.

## C25 direct Nucleus recursor replay-key overhead (CANDIDATE, awaiting native run)

On the same C18 original `magma-list-pair-n7`, a read-only trace of the exact C18 native binary `e5f1329ab1228a2aadd3fa5b0f79f7595fd0c70ded874d59788b171b90cbe2df` recorded 32 limited `NUCLEUS_REPLAY_WORK` segments: 1,081 units attributed to key traversal/copy/hash reservation out of 2,022 measured consumed units **within this possibly nested sample**. These cannot be summed into a global cost percentage; they identify a specific source-qualified local-work target. N7's unchanged final countermodel remains UNKNOWN with a registered-recursors obstruction while global steps remain largely unused.

C25 [new native run #42444253785](https://github.com/heathsanchez/test/actions/runs/42444253785) (PENDING) tests a *diagnostic-only* skip of exact replay-key construction/lookup/retention, leaving each registered source recursor, selected constructor, iota RHS, source projection, and shared metered work owner intact. A skipped key cannot serve as a proof or reusable equality. With the C18 verified binary and new toggle set, the RED preflight produced unchanged n7 exit 2 and zero `NUCLEUS_REPLAY_KEYLESS_SOURCE` events; C25 must exercise that event on all four SHA-frozen Magma originals and preserve default-OFF source and protected regressions. No claim of four-case or six-case closure is made before native evidence. If the key-free experiment remains UNKNOWN, reject the key overhead as a sufficient obstruction and stop trying scalar cap tuning.


## C24 combined memo-ablation interaction complete (REFERENCE ONLY)

[C24 run #42443995624](https://github.com/heathsanchez/test/actions/runs/42443995624), commit `10cb49d90bbc1acc74636b1094bfdd49a070581a`, **SUCCESS**, artifact `13602324602`, verified ZIP SHA256 `6276e3da1d0edb359c173156c15e959f6c6c0efa65ad92cea9aaada0f3cbc1bb`. This completes the planned 2×2 reference factorial on *identical original, source-hashed* `fueled-chain`: (both memo caches on), (Pi-instantiation memo off), (closed-expression type memo off), and (both off). The combined stage rebuilds the pinned nano source with **both** tracked C22 and C23 patches applied after reversing the isolated C23 test. All four stages return reference exit **0 / ACCEPT** at the external `--steps 262144` setting; the two exact counter gates scan all 113 native declaration records and verify `inst_hit=0` and `closed_hit=0` in the combined stage.

For combined `chain12_datF`: `applies=122,839`, `memo_hits=192,950`, `deq_ptr_eq=108,167`, `fires=190`, `inst_hit=0`, `closed_hit=0`, `closed_miss=112,727`. The `exhausted=1` internal event occurred even though the overall declaration **ACCEPTED**; do not mistake one recoverable internal exhaustion counter for an UNKNOWN verdict. **REJECTED** at this external diagnostic boundary: either memo individually **or their combined availability** is necessary for acceptance. These two particular caches are no longer a justified first-fix strategy for Nucleus. The reference's other memoization, value interning, certified reduction and dynamic firing remain unisolated and its trust prelude remains absent. Its resource meter is not Nucleus's standard charged-step semantics; no source-qualified Nucleus ACCEPT or Mathlib completion is promoted. Pivot to actual Nucleus registered recursor and local work-owner obstruction instead of repeating the reference cache search.


## C25 source-qualified keyless replay: four original UNKNOWNs unchanged

[C25 run #42444253785](https://github.com/heathsanchez/test/actions/runs/42444253785), commit `6907aa8e6a403ee1e525d5888f00922cb348e9fb`, **SUCCESS**, artifact `13603320379`, verified ZIP SHA256 `efa05a6c8e2feffe0cc6c2cb4905aa04b84f3ac5f1ebf02dbe114511ac3003aa`. Its exact source patch `c25-source-checked-keyless-worklist.patch` applies without fuzz after the independently qualified C11–C18 source patches. Native proof/adversarial checks passed, isolated `app-lam` stack controls remained ACCEPT, and the protected **403/403** unchanged default-flag verdict vector matched the selected **240 ACCEPT / 150 REJECT / 13 UNKNOWN**. The C25 keyless toggle was **OFF** for the 403-case vector; do not misreport this as a keyless-on adversarial qualification.

With `NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS=1` ON, all four unchanged and SHA-checked original Magma cases returned exit **2 / UNKNOWN**: pair-n7 (157 keyless source events), pair-n21 (159), deep-n21 (535), deep-n36 (475). There were **zero** new original ACCEPTs. The control binary C18 had been tested RED: n7 exit2 and zero C25 events. A new direct Nucleus replay of the exact C25 release binary `b6cab0012f1d2209548579fd24bd6652a5b4caafc0ba0fbb7ee3b14ec4846d62` with selected flags plus keyless and diagnostic traces confirmed `NUCLEUS_REPLAY_WORK ... key_work=0` on the final local Nat.rec segments, but the actual `major_expr=ExprId(6)` still exhausted the shared exposure owner at an actual source `BVar(1)` captured as another `BVar(1)` closure in a different source environment. The unchanged n7 ended at `countermodel:definition.value:application-function-type` UNKNOWN. This separates *memo-key overhead* from the real stuck source-major exposure; the former is insufficient to close any of the four under this intervention.

**Status:** C25 is WARRANTED_BOUNDED for native qualification in the default mode and negative original valid results with the diagnostic flag ON. It is **REJECTED** as a closure intervention; not promoted to the selected independent kernel. The no-key mode simultaneously removes key-work and completed-key-cache reuse, so an UNKNOWN does not prove key costs can never matter in another design. One consequential missing distinction remains: does the captured major's *actual source binding chain* terminate in a constructor, a rigid free local, or a cycle/over-budget prefix? Until that is measured, no amount of cap tuning or cache-key bypass warrants guessing an iota result. Four original Magma and the two other original valid UNKNOWNs remain open; source-qualified complete Mathlib is also open.


## C26 actual source-major binding-chain census: long-chain hypothesis rejected

[C26 run #42444977770](https://github.com/heathsanchez/test/actions/runs/42444977770), workflow commit `5b29b4e9d2a730bf85ef6b921466c1def7042bc3`, **SUCCESS**, artifact `13603336698`, independently downloaded ZIP SHA256 `45a01733bb096a3bc0a89b300427e9935e0fb694169cf61cfbc8d66ac38b04ef`. The source-only `c26-source-major-chain-census.patch` is diagnostic, opt-in (`NUCLEUS_DIAGNOSTIC_MAJOR_CHAIN`), and does not return proof values, infer constructors or alter comparison rules. A C25 binary was tested RED with the diagnostic flag: zero `NUCLEUS_SOURCE_MAJOR_CHAIN` reports despite native UNKNOWN and existing replay failures. C26 compiled, ran native proof/adversarial controls, and reproduced the default-mode original **403/403** verdict vector unchanged: **240 ACCEPT / 150 REJECT / 13 UNKNOWN**. The 403 controls did *not* enable the C26 observer flag.

All four SHA-pinned unchanged original Magma inputs returned **UNKNOWN** under both normal keyed replay and C25's diagnostic keyless mode (eight native input/mode combinations). Every logged failing major (all **57**, with no output cap reached) had a concrete source closure chain resolving within **7 hops**: **20** terminate in an actual rigid `FreeId` binding and **37** terminate in a source application. No cycles, missing bindings, 65,536-hop caps or terminal constructors were observed. The applicative head includes `Nat.add` on pair exports and `Nat.ble`, `Nat.decLt`, `instDecidableEqBool` on deep exports; one application begins with a source projection. These names were decoded from the **same unchanged input export's name table**, not guessed from trace IDs. A source application *may* still compute a constructor; syntax alone does not warrant assuming a permanently stuck major.

Most consequentially, **56/57** observed failures came from the **optional qualified one-step recursor probe in `src/convert.rs:1862`** (same-head, differing-spine neutral comparison), while just one came from `src/convert.rs:2046`. Those per-probe UNKNOWNs are not necessarily the final reason the declaration is UNKNOWN; they identify a high-cost candidate path for causal intervention. The failed-long-binding-chain hypothesis is **REJECTED** for these specific qualified traces, so do not optimize BVar path compression as the next fix. C26 is **WARRANTED_BOUNDED** as diagnostic evidence only. The smallest next experiment is a strict pre-iota exact-source congruence **observation** on those same-head recursors: test whether an already source-checked argument congruence can succeed before the speculative iota probe spends its local allowance. No acceptance semantics may change until a separate candidate passes complete protected qualifications. Six standard original UNKNOWNs and complete Mathlib remain **UNKNOWN**.


## C27 source-only pre-iota relational congruence observer: positive certificates, not acceptance

[C27 run #42445806162](https://github.com/heathsanchez/test/actions/runs/42445806162) **SUCCESS**, workflow commit `bb931944d86d55bad8712212a5f83357a8703279`, artifact `13602949090`, independently downloaded ZIP SHA256 `aec58adcd8330976b932789c7f4d7a200197f02ef2b62d24f05f550ed5e4aad0`. The C27 source-only patch `c27-pre-iota-source-congruence-observer.patch` calls the **existing pure `relational_source_substitution` implementation** on all captured arguments only when two registered recursor neutral heads are already structurally identical. The trial runs before optional iota and is separately bounded to 4096 source-work units; it does **not** grant equality, alter metered conversion work, persist source-capture facts, or change default proof logic. The previous exact C26 binary was RED (0 C27 markers); the C27 native candidate was GREEN, with all four original valid Magma cases still UNKNOWN (exit2) and default observer-OFF **403/403** unchanged (240 ACCEPT / 150 REJECT / 13 UNKNOWN). Native proof/adversarial suites passed. Observer-ON 403 regressions have **not** been separately run, and cannot be implied from the default outcome vector.

The unexpected **positive sufficiency** is real but bounded: unchanged pair-n7 and pair-n21 each had **12/25** observed pre-iota pairs source-relational PROVEN; unchanged deep-n21 and deep-n36 each had **20/128** PROVEN (128-event cap; no total rate inferred). All 64 positives across the four separate native runs concern actual same-head source-neutral applications; none required literal closure identity (`identical=0` in representative n7 records), but the independently checked simultaneous source substitution related their captured terms. For n7, 11/12 positive proofs consumed **at most 512** source steps (range 183–1599); for each deep case, 18/20 consumed at most 512 (range 183–809). The rest fail bounded checks; the witness proves a sufficient congruence for only those specific source captures, **not** a constructor, a recursor result, or the enclosing declaration.

**C28 cheapest consequential intervention:** under a separate opt-in flag, attempt this same source-exact congruence before speculative recursor one-step replay, charge all attempted source work to the actual caller, and return conversion PROVEN only on a completed same-head/same-universe/all-argument certificate. Every failure falls back to unchanged conversion with remaining budget. Require exact frozen original valid and forged input replays plus a full **flag-ON** protected 403-case regression. C27 is **WARRANTED_BOUNDED** for the positive observer findings and **UNKNOWN** as a route to a standard-budget Nucleus ACCEPT until C28 or other causal interventions are qualified. The actual final Bool-vs-Decidable full replay remains distinct from the 56 speculative C26 side probes.


## C28 source-certified congruence-first: protected but no declaration closure

[C28 native run #42446706998](https://github.com/heathsanchez/test/actions/runs/42446706998) **SUCCESS** at workflow commit `4210d5a73d611d910803aac96bb460a52253f24d`; artifact `13603149323`, independently retrieved and SHA256 verified as `05802a730cb98af7b0e98872fdcc6792ed9382da8f9c8eed66c7bdae734b7076`. The exactly replayed C27-selected source received only opt-in `c28-source-certified-pre-iota-congruence.patch`; no selected 24 flags, original proof bytes, source recursor rules, or standard 262144-step global budget changed. Rust check, native proof/adversarial tests, chain9, app-lam, and all source diagnostics passed. The *default* and explicitly *C28 flag-ON* protected **403/403** both retained precisely **240 ACCEPT / 150 REJECT / 13 UNKNOWN**, with **zero outcome changes** across cases, including forged proofs. This is a bounded regression statement, not general soundness proof.

The source-first candidate confirms all actual captured arguments via the preexisting pure `relational_source_substitution` (same registered head, same instantiated universes), charges source-comparison work directly to the current comparison allowance, and only returns PROVEN after every argument succeeds. It declines under a nested exposure owner to avoid an uncharged second owner. Failed trials continue with the remaining allowance and the old qualified replay. The opt-in was genuinely active: a total **124** successful local source-congruence certificates in **502 logged bounded trials** across six separate unchanged-valid replays (only the first 128 are logged for each of fueled-chain and grind-ring-5):

| Unchanged valid original | C28 verdict | Logged source trials | Locally PROVEN |
|---|---:|---:|---:|
| fueled-chain | UNKNOWN (2) | 128 (capped) | 3 |
| grind-ring-5 | UNKNOWN (2) | 128 (capped) | 43 |
| magma-list-pair-n7 | UNKNOWN (2) | 22 | 6 |
| magma-list-pair-n21 | UNKNOWN (2) | 22 | 6 |
| magma-list-deep-n21 | UNKNOWN (2) | 101 | 33 |
| magma-list-deep-n36 | UNKNOWN (2) | 101 | 33 |

No original declaration became ACCEPT. No proof result came from an expected constructor or cached semantic assumption. The entire 403-case summed per-case wall sample was 100.593 seconds default vs 102.841 seconds C28 ON; this is **not** a replicated benchmark or speed improvement. **C28 is WARRANTED_BOUNDED for the guarded source-level subproofs and regression boundary, but REJECTED as a sufficient six-case closure intervention.** Keep the selected default mode unchanged. This causal negative prevents spending further rounds optimizing the 56 optional C26 recursor side probes without first showing they obstruct final acceptance.

A separate exact-local-source native diagnostic (artifact binary SHA256 `29c77d0aad933277743253e301fe8cd21ecdcd396d5726bb67dacfd5c6bab55c`, pinned six input hashes above, original 24 flags, additional read-only `NUCLEUS_TRACE_DOWNSTREAM=1` and `NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE=1`) isolated the *actual outer residual*. Five of six emit final `application-function-type`; deep-n21 emits `unresolved-qualified-recursor-heads`. Pair-n7 and pair-n21's outer `countermodel` application fails function-type inference with underlying `unresolved-qualified-recursor-heads` despite **261687 / 261783 remaining outer steps**, respectively. In n7, `NUCLEUS_TRACE_NEUTRAL_HEADS=1` reveals a certified **Bool.true** (NameId169) versus a still-unreduced, five-argument **Decidable.rec** (NameId147) at a **260755-step** comparison grant. Deep-n36 also exhibits an inner `rigid-type-constructor-mismatch`; fueled-chain records a later inner application at **0** remaining steps. Those are different terminal mechanisms even though five surface residual labels match. The local flags add observations only; these *diagnostic hypotheses* need a separate native artifact before promoting deeper causal claims.

**C29 smallest decisive experiment:** isolate the actual large-budget *completed* `Decidable.rec` major replay for pair-n7/n21, tracing the exact source-major work-owner consumption and the first source-relevant irreducibility/projection obligation. Do not infer a constructor from the expected Bool.true, reuse a cross-context type, or spend another cycle on keyless/repeated optional probe counts alone. Test one source-certified change at a time against all six SHA-pinned originals and both default/flag-ON protected regressions. Complete Mathlib and all six standard-budget inputs remain **UNKNOWN**.


**Controlled C28+C25 composition, source-pinned local negative:** on the same extracted C28 native artifact and unchanged 24 flags, setting both `NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE=1` and `NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS=1` still returned exit2 UNKNOWN for exact original pair-n7 and grind-ring-5 (their SHA256s are the table entries above). Pair-n7's trace made a useful two-stage distinction: keyed large-budget `Decidable.rec` completed replay with grant 260755 returned `nested-replay-key-work`; removing keys moved the same grant to `nested-recursor-iota-budget`, and a source-qualified one-step replay at grant 130377 exhausted its owner with another five-argument qualified `Decidable.rec` still neutral at depth 65. Thus key work is *a* real blocker, but eliminating that key work plus C28's locally proved congruence is not sufficient. The grind combined result likewise remained UNKNOWN after approximately 47 seconds, not a performance warrant. This bounded composition is **REJECTED as a closure intervention**; prioritize the actual nested reduction/worklist progress measure over more independent key or congruence toggles. These two local replays have not undergone a separate flag-combination 403 regression, so they confer no new acceptance authority.
