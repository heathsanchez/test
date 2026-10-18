# Prospective source-distinct G2 V3 — Trio admission stops before method execution

**Scientific status:** `UNKNOWN_NO_AUTHENTIC_TRAINING_PROTECTED_FAILURE`  
**Prospective G2:** UNKNOWN  
**Future source:** UNOPENED

## Frozen lineage

- Prequery protocol: `6b96a5dcb5fcdd449639ba09aa5fbd600da0524a`
- Metadata-only role freeze: `4c5670f489c9c435f1f47d706f6dca8373d6fa96`
- Final pre-native apparatus freeze: `083ece67095b2815851228ab423864b4eb500fb6`
- Qualified workflow head: `52deacad755d6c73b3940a0a411bbc03dcd1cd35`
- Hosted run: https://github.com/heathsanchez/test/actions/runs/39096319268
- Classification artifact: `12125275446`, ZIP digest `sha256:2d9b9b9a69c0dadd4131b513a28bc58b995ac91040eafe7a64fde39f0f736c7c`
- CPython artifact: `12125100865`, ZIP digest `sha256:ad49578e3e75ea070dc452401500d4fca9d8f8072b3f4c70de54311eac944b9f`
- PyPy artifact: `12124965739`, ZIP digest `sha256:0b4f61b95e92cc70d71fd53bd7e46d45b034c5ce01bb7ba4717ea56415bb986c`

## Role selection

The role selection was frozen before source-body/native exposure.

**TRAINING:** `python-trio/trio#3525`  
Base `ada9c778c86f35c62e68bae8284ca652ea2b23c2`; author-test commit `e12547f78849be25ec5c0c1a3df161986be1ae96`; production `src/trio/socket.py`; changed author test `src/trio/_tests/test_exports.py`.

**HELDOUT_FUTURE:** `pytest-dev/pluggy#755`  
Base/head metadata were frozen, but source/test bodies were never opened and no native future call ran.

The selection rule used only merged-PR metadata and changed filenames. No source patch or repaired production was read before role freeze.

## Exact native training result

The original Trio base plus the exact changed author-test file was executed on both frozen Python 3.11 implementations, with both ordinary and repository `--run-slow` modes.

### CPython 3.11

- Default: **17 passed / 29 skipped / 0 failed / 0 errors**, 46 collected.
- `--run-slow`: **45 passed / 1 skipped / 0 failed / 0 errors**, 46 collected.
- Source-neutral mutable-closure pattern count: **0**.

### PyPy 3.11

- Default: **10 passed / 36 skipped / 0 failed / 0 errors**, 46 collected.
- `--run-slow`: **17 passed / 29 skipped / 0 failed / 0 errors**, 46 collected.
- Source-neutral mutable-closure pattern count: **0**.

Therefore there is **no authentic failing training obligation** under the frozen source/test/runtime boundary. The repaired AnyIO method was correctly **not executed**. Pluggy remained sealed.

## What this means

This is **not** evidence against the AnyIO mutable-closure observer/repair method. The method never received a qualifying residual.

It falsifies a weaker assumption in the prospective task-selection protocol: a merged PR whose title starts with `fix`, with one production Python file and changed Python tests, is **not sufficient to guarantee that original production + head author-test overlay yields a failing protected obligation**. Here the selected test delta is compatibility/suppression logic and the original source remains green.

The next protocol must separate:

1. **source-blind metadata selection of a candidate pool**;
2. **source-native obligation admission** (original production + exact author test must FAIL);
3. only then **method qualification**;
4. only after training method qualification, open a separately frozen future.

Candidates that are natively PASS are admission rejections, not method failures and not substitutes chosen after outcome. A deterministic frozen pool/order can preserve non-cherry-picking while walking until the first authentic native failure.

## Apparatus lineage

Earlier runs on this branch failed before native science due:
- porcelain status whitespace parsing;
- PyPy `cffi` / `pycparser` dependency mismatch.

Both were repaired and frozen before successful native execution. They are apparatus NON_EVIDENCE.

## Boundary

G2–G6 remain UNKNOWN. No future source was read, no future native test was executed, no matched ledger/agent comparison ran, and no cross-source repair was attempted.
