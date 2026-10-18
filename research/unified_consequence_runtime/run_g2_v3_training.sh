#!/usr/bin/env bash
# Frozen prospective G2 V3 TRAINING-only: original Trio source, future Pluggy sealed.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 GIT_NO_REPLACE_OBJECTS=1 GIT_OPTIONAL_LOCKS=0
ROOT="${GITHUB_WORKSPACE:-$PWD}"
cd "$ROOT"
E="$ROOT/evidence/g2-v3"
mkdir -p "$E"
P=research/unified_consequence_runtime
BASE=ada9c778c86f35c62e68bae8284ca652ea2b23c2
HEAD=e12547f78849be25ec5c0c1a3df161986be1ae96
TEST=src/trio/_tests/test_exports.py
TRAIN=/tmp/g2-v3-train
V104=/tmp/g2-v3-v104
MSI=/tmp/g2-v3-msi

cmp "$P/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_PROTOCOL.json" <(git show 6b96a5dcb5fcdd449639ba09aa5fbd600da0524a:"$P/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_PROTOCOL.json")
cmp "$P/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_ROLE_FREEZE.json" <(git show 4c5670f489c9c435f1f47d706f6dca8373d6fa96:"$P/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_ROLE_FREEZE.json")
for f in G2_MUTABLE_CLOSURE_EQUIVALENCE_FIX_PROTOCOL_V2.json g2_mutable_closure_trace_plugin_v2.py g2_anyio_mutable_closure_equivalence_fix_v2.py qualify_g2_anyio_mutable_closure_equivalence_fix_v2.py; do
  cmp "$P/$f" <(git show 094e2ddc3ba601a00eaf368151172a361e5542da:"$P/$f")
done
python -B -m py_compile "$P/g2_prospective_source_distinct_v3_training.py" "$P/qualify_g2_prospective_source_distinct_v3_training.py"
sha256sum "$P/G2_PROSPECTIVE_SOURCE_DISTINCT_V3_ROLE_FREEZE.json" "$P/G2_V3_ENVIRONMENT_ADMISSION_FREEZE.json" > "$E/CONTROL_HASHES.txt"
printf '%s\n' 'TRAINING python-trio/trio#3525' 'FUTURE pytest-dev/pluggy#755 SEALED_UNOPENED' > "$E/ROLE_BOUNDARY.txt"
echo SOURCE_AND_METHOD_FROZEN

# Fetch only source-pinned original base and one head-authored TEST file.
git init -q "$TRAIN"
git -C "$TRAIN" remote add upstream https://github.com/python-trio/trio.git
git -C "$TRAIN" fetch -q --depth=1 --no-tags --filter=blob:none upstream "$BASE"
git -C "$TRAIN" checkout -q --detach "$BASE"
git -C "$TRAIN" fetch -q --depth=1 --no-tags --filter=blob:none upstream "$HEAD"
test "$(git -C "$TRAIN" rev-parse HEAD)" = "$BASE"
git -C "$TRAIN" show "$BASE:$TEST" > /tmp/g2-v3-base-test.py
git -C "$TRAIN" show "$HEAD:$TEST" > /tmp/g2-v3-head-test.py
cp /tmp/g2-v3-head-test.py "$TRAIN/$TEST"
test "$(git -C "$TRAIN" diff --name-only)" = "$TEST"
sha256sum "$TRAIN/src/trio/socket.py" /tmp/g2-v3-base-test.py /tmp/g2-v3-head-test.py > "$E/TRAINING_SOURCE_HASHES.txt"
echo 'pytest-dev/pluggy PR755 UNOPENED' > "$E/FUTURE_SEAL.txt"
echo ORIGINAL_TRAINING_SOURCE_BOUND

# Environment order was separately frozen before source read.
python -m pip install --disable-pip-version-check --no-input 'pip==25.3'
python -m pip install --disable-pip-version-check --no-input -e "$TRAIN"
supplement="$(python - <<'PY'
import pathlib,tomllib
root=pathlib.Path('/tmp/g2-v3-train')
p=root/'pyproject.toml'
d=tomllib.loads(p.read_text()) if p.is_file() else {}
g=d.get('dependency-groups',{})
e=d.get('project',{}).get('optional-dependencies',{})
if 'test' in g: print('GROUP:test')
elif 'tests' in g: print('GROUP:tests')
elif (root/'test-requirements.txt').is_file(): print('FILE:test-requirements.txt')
elif (root/'requirements-test.txt').is_file(): print('FILE:requirements-test.txt')
elif 'test' in e: print('EXTRA:test')
elif 'tests' in e: print('EXTRA:tests')
elif 'dev' in e: print('EXTRA:dev')
else: print('NONE')
PY
)"
echo "$supplement" | tee "$E/TEST_SUPPLEMENT.txt"
case "$supplement" in
  GROUP:test) python -m pip install --no-input --group "$TRAIN/pyproject.toml:test";;
  GROUP:tests) python -m pip install --no-input --group "$TRAIN/pyproject.toml:tests";;
  FILE:test-requirements.txt) python -m pip install --no-input -r "$TRAIN/test-requirements.txt";;
  FILE:requirements-test.txt) python -m pip install --no-input -r "$TRAIN/requirements-test.txt";;
  EXTRA:test) python -m pip install --no-input -e "$TRAIN[test]";;
  EXTRA:tests) python -m pip install --no-input -e "$TRAIN[tests]";;
  EXTRA:dev) python -m pip install --no-input -e "$TRAIN[dev]";;
  NONE) :;;
  *) exit 23;;
esac
python -m pip install --disable-pip-version-check --no-input 'pytest==9.1.1' 'pytest-cov==7.0.0'
python -m pip check
python -m pip freeze > "$E/PIP_FREEZE.txt"

# Exact prequalified original V104 and MSI method authority.
git init -q "$V104"
git -C "$V104" fetch -q --depth=1 https://github.com/heathsanchez/triskelion.git 426c54f7c774560e0fabe7213c5ef333b1327c71
git -C "$V104" checkout -q --detach 426c54f7c774560e0fabe7213c5ef333b1327c71
git init -q "$MSI"
git -C "$MSI" fetch -q --depth=1 https://github.com/heathsanchez/Minimal-Sufficient-Interface.git 56cfd7b523e3592cae4eafa5468f437ccb94dbe9
git -C "$MSI" checkout -q --detach 56cfd7b523e3592cae4eafa5468f437ccb94dbe9

set +e
PYTHONPATH="$ROOT" python -B "$P/g2_prospective_source_distinct_v3_training.py" \
  "$TRAIN" "$V104" "$MSI" /tmp/g2-v3-base-test.py /tmp/g2-v3-head-test.py \
  "$RUNNER_TEMP/g2-v3-training" | tee "$E/SCIENCE_STDOUT.json"
science_exit=${PIPESTATUS[0]}
set -e
if [ -d "$RUNNER_TEMP/g2-v3-training" ]; then
  cp -a "$RUNNER_TEMP/g2-v3-training" "$E/training"
fi
if [ "$science_exit" -ne 0 ]; then exit "$science_exit"; fi
python -B "$P/qualify_g2_prospective_source_distinct_v3_training.py" \
  "$E/training/RESULT.json" "$TRAIN" "$E/INDEPENDENT_CHECK.json"
echo "SCIENCE_VERDICT_RECORDED_FUTURE_UNOPENED"
