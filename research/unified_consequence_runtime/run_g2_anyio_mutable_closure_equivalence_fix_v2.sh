#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
EVIDENCE="$ROOT/evidence/g2-anyio-v2"
RESULT_ROOT="${RUNNER_TEMP:-/tmp}/g2-anyio-v2-result"
ANYIO=/tmp/udm-anyio-v2
V104=/tmp/udm-v104-v2
MSI=/tmp/udm-msi-v2
PROTOCOL=research/unified_consequence_runtime/G2_MUTABLE_CLOSURE_EQUIVALENCE_FIX_PROTOCOL_V2.json
PROTOCOL_COMMIT=7cc32cabf2f749e13aa7813fb2dc62cfb1a1d9ff

rm -rf "$EVIDENCE" "$RESULT_ROOT" "$ANYIO" "$V104" "$MSI"
mkdir -p "$EVIDENCE"

cmp "$PROTOCOL" <(git show "$PROTOCOL_COMMIT:$PROTOCOL")
python -B -m py_compile \
  research/unified_consequence_runtime/g2_mutable_closure_trace_plugin_v2.py \
  research/unified_consequence_runtime/g2_anyio_mutable_closure_equivalence_fix_v2.py \
  research/unified_consequence_runtime/qualify_g2_anyio_mutable_closure_equivalence_fix_v2.py

git rev-parse HEAD > "$EVIDENCE/EXPERIMENT_HEAD.txt"
sha256sum "$PROTOCOL" \
  research/unified_consequence_runtime/g2_mutable_closure_trace_plugin_v2.py \
  research/unified_consequence_runtime/g2_anyio_mutable_closure_equivalence_fix_v2.py \
  research/unified_consequence_runtime/qualify_g2_anyio_mutable_closure_equivalence_fix_v2.py \
  > "$EVIDENCE/EXPERIMENT_SOURCE_SHA256.txt"
echo PASS_PREIMPLEMENTATION_PROTOCOL_BINDING

git init -q "$ANYIO"
git -C "$ANYIO" remote add upstream https://github.com/agronholm/anyio.git
git -C "$ANYIO" fetch -q --depth=1 --filter=blob:none --no-tags upstream 1805944a9f6a062527c10aa044ded959782bfc3e
git -C "$ANYIO" checkout -q --detach 1805944a9f6a062527c10aa044ded959782bfc3e
test "$(git -C "$ANYIO" rev-parse HEAD^{tree})" = c6465ce4b900e2f21aa73ebbe16c779f5c6ae9bf
git -C "$ANYIO" fetch -q --depth=1 --filter=blob:none --no-tags upstream 90876855b731fb057d45e7e1cbdf1df013be6091
test "$(git -C "$ANYIO" rev-parse 90876855b731fb057d45e7e1cbdf1df013be6091:tests/test_pytest_plugin.py)" = b15d4da74a17b7f80fa07b0d172c03eb752be7f4
git -C "$ANYIO" show 90876855b731fb057d45e7e1cbdf1df013be6091:tests/test_pytest_plugin.py > "$ANYIO/tests/test_pytest_plugin.py"
echo "a0b5f23acb6f4595b75556ea20e0e166c3ede234b3d941a1e3861e1b69c95f1d  $ANYIO/src/anyio/pytest_plugin.py" | sha256sum -c -
echo "c7dc03febccc7d17bc8291cd7ace6cbe7e87da8350434bbf88f1b9b26033b5fe  $ANYIO/tests/test_pytest_plugin.py" | sha256sum -c -
test "$(git -C "$ANYIO" diff --name-only)" = tests/test_pytest_plugin.py
echo PASS_ORIGINAL_SOURCE_PLUS_AUTHOR_TEST_ONLY

git init -q "$V104"
git -C "$V104" fetch -q --depth=1 https://github.com/heathsanchez/triskelion.git 426c54f7c774560e0fabe7213c5ef333b1327c71
git -C "$V104" checkout -q --detach 426c54f7c774560e0fabe7213c5ef333b1327c71
git init -q "$MSI"
git -C "$MSI" fetch -q --depth=1 https://github.com/heathsanchez/Minimal-Sufficient-Interface.git 56cfd7b523e3592cae4eafa5468f437ccb94dbe9
git -C "$MSI" checkout -q --detach 56cfd7b523e3592cae4eafa5468f437ccb94dbe9
test "$(git -C "$V104" rev-parse HEAD)" = 426c54f7c774560e0fabe7213c5ef333b1327c71
test "$(git -C "$MSI" rev-parse HEAD)" = 56cfd7b523e3592cae4eafa5468f437ccb94dbe9
echo PASS_PINNED_METHOD_AUTHORITIES

python -m pip install --disable-pip-version-check --no-input 'pip==25.3'
python -m pip install --disable-pip-version-check --no-input \
  -e "$ANYIO[trio]" \
  --group "$ANYIO/pyproject.toml:test" \
  'pytest==9.1.1' 'pytest-cov==7.0.0'
python -m pip check
python -m pip freeze > "$EVIDENCE/PIP_FREEZE.txt"

PYTHONPATH="$ROOT" python -B \
  research/unified_consequence_runtime/g2_anyio_mutable_closure_equivalence_fix_v2.py \
  "$ANYIO" "$V104" "$MSI" "$RESULT_ROOT" \
  | tee "$EVIDENCE/STDOUT.json"
cp -a "$RESULT_ROOT" "$EVIDENCE/result"

python -B \
  research/unified_consequence_runtime/qualify_g2_anyio_mutable_closure_equivalence_fix_v2.py \
  "$EVIDENCE/result" "$ANYIO" "$EVIDENCE/INDEPENDENT_QUALIFICATION.json"

echo PASS_G2_ANYIO_V2_RUNNER
