# AnyIO G2 mutable-closure / equivalence-class repair V2

**Status:** WARRANTED_BOUNDED_POSTHOC_TRAINING_REPAIR_AND_CLASS_SELECTOR  
**Prospective G2:** UNKNOWN  
**Held-out future:** UNOPENED

## Exact authority

- Branch: `research/udm-anyio-mutable-closure-equivalence-fix-v2-20261018`
- Qualified executable head: `094e2ddc3ba601a00eaf368151172a361e5542da`
- Hosted run: https://github.com/heathsanchez/test/actions/runs/39093934449
- Artifact: `12123712928`
- Artifact ZIP digest: `sha256:3689e93c67b23378642947eaba710a2d4eb7685025d417a11eeeb28aeef77b75`
- Frozen pre-implementation protocol: `7cc32cabf2f749e13aa7813fb2dc62cfb1a1d9ff`
- AnyIO production source: `agronholm/anyio@1805944a9f6a062527c10aa044ded959782bfc3e`
- Author-test object: `agronholm/anyio@90876855b731fb057d45e7e1cbdf1df013be6091:tests/test_pytest_plugin.py`
- V104 method pin: `heathsanchez/triskelion@426c54f7c774560e0fabe7213c5ef333b1327c71`
- MSI method pin: `heathsanchez/Minimal-Sufficient-Interface@56cfd7b523e3592cae4eafa5468f437ccb94dbe9`

The experiment did **not** read repaired upstream production or the previously sealed `alexmojaki/executing#50` future.

## What was fixed

The original frozen G2 gate treated 37 named scheduling policies as independent competitors. The exact first-eight-candidate audit proves that these names quotient to only two behavioral classes:

1. the cold V104 order; and
2. one noncold class containing all 36 MSI-named policies.

Therefore strict uniqueness over policy names was structurally impossible. V2 makes the **equivalence class** the authorization unit; a representative name is display metadata and carries no authority.

The source-neutral scanner also finds one exact persistent nested-closure pattern in the original AnyIO production source. The nested pytest observer records the same generated wrapper object being written after the `asyncio` invocation and read again for the subsequent `trio` invocation. Its retained closure contains `backend_name="asyncio"`. This is native evidence for cross-invocation stale closure state on the protected failure, rather than the earlier local simulation.

## Generated repair

The frozen method generates one deterministic candidate from the observed pattern. It inserts five lines immediately after the persistent callable is read:

- recognize that the stored callable is the source hook's own nested wrapper;
- recover the wrapper's closure cells;
- take the closure cell corresponding to the source callable that was wrapped;
- restore that underlying callable locally;
- let the **existing source guard** rebuild a wrapper using the current invocation context.

Variable names, attribute path, wrapper identity and captured-source name are derived from the detected AST pattern. The generator contains no AnyIO function name, line number, backend name, test name, or known repaired-source bytes.

## Native causal gate

Original source + exact author test overlay:
- protected tests: **0 PASS / 2 FAIL**.

Generated repair:
- protected run A: **2/2 PASS**;
- protected run B: **2/2 PASS**;
- complete `tests/test_pytest_plugin.py`: **42/42 PASS**, zero failures/errors/skips.

Physical withdrawal:
- exact original production restored;
- protected tests return to **0 PASS / 2 FAIL**.

Exact restoration:
- byte-identical generated repair reapplied;
- protected tests return to **2/2 PASS**.

Independent qualification additionally proves the generated production differs from the frozen original by exactly one five-line insertion.

## Epistemic boundary

This warrants a bounded result on the already-exposed AnyIO training case:

> a source-neutral persistent-closure observation can generate a causally necessary and sufficient repair for the authentic protected failure, and scheduling aliases must be quotiented before selection.

It does **not** establish prospective G2, cross-repository transfer, arbitrary mutable-state repair, unrestricted constructor invention, or G3-G6. Those remain UNKNOWN.

## Supersession / negative lineage

- The frozen 36-way named-policy unique-winner gate is **REJECTED / SUPERSEDED**.
- The earlier posthoc local simulation is **SUPERSEDED as the strongest training evidence** by this native protected-test observation.
- Early V2 red runs that produced zero observer events are apparatus lineage: they exposed decorated-function line binding and nested-Pytester observation boundaries. They do not refute the mutable-closure hypothesis; the corrected frozen-method implementation subsequently observed and repaired it natively.
- Existing failed V104 source-locality results remain valid: the original 64 candidates do not repair this failure.

## Next decisive experiment

Freeze a **new source-distinct training/future pair** before reading source bodies or native outcomes, while keeping this observer, repair constructor and equivalence-class selection method fixed. Require:

1. the method to discover a source-local native obstruction without supplied repair coordinates;
2. independent native repair qualification and physical withdrawal;
3. prospective reuse or second-generation acquisition on the sealed future;
4. matched informed baselines and full acquisition/verification cost accounting.

Until that gate passes, **G2 remains UNKNOWN**.
