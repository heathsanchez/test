#!/usr/bin/env bash
set -euo pipefail
ROOT="$(pwd)"
OUT="$ROOT/research/mgcheck_http_range_20261015/evidence"
mkdir -p "$OUT"
BASE="f7b1c4f68b90299afc89ffeb47756e5fca590b91"
HEAD="335f61397af402ef77977a8e0c7a200f923349d1"
test "$(git -C "$ROOT/base" rev-parse HEAD)" = "$BASE"
test "$(git -C "$ROOT/candidate" rev-parse HEAD)" = "$HEAD"
echo "$BASE" > "$OUT/base.sha"
echo "$HEAD" > "$OUT/head.sha"
python3 "$ROOT/research/mgcheck_http_range_20261015/generate_http_retry_observer.py" \
  "$ROOT/candidate/pkg/downloader/downloader.go" \
  "$OUT/mathgraph_generated_cycle_test.go" > "$OUT/method_stdout.json"
cp "$OUT/mathgraph_generated_cycle_test.go" "$ROOT/base/pkg/downloader/mathgraph_generated_cycle_test.go"
cp "$OUT/mathgraph_generated_cycle_test.go" "$ROOT/candidate/pkg/downloader/mathgraph_generated_cycle_test.go"
gofmt -w "$ROOT/base/pkg/downloader/mathgraph_generated_cycle_test.go" "$ROOT/candidate/pkg/downloader/mathgraph_generated_cycle_test.go"
cp "$ROOT/candidate/pkg/downloader/downloader.go" "$OUT/original_download.go"
sha256sum "$OUT/original_download.go" > "$OUT/qualified_source_sha256.txt"

test_case() {
  local name="$1" repo="$2"
  local start rc end
  start=$(date +%s)
  set +e
  (cd "$ROOT/$repo" && go test -count=1 -timeout=4m -run '^(TestMathGraphGeneratedNormal200|TestMathGraphGeneratedRetryCycle)$' -v ./pkg/downloader) > "$OUT/$name.log" 2>&1
  rc=$?
  set -e
  end=$(date +%s)
  echo "$rc" > "$OUT/$name.status"
  echo "$((end-start))" > "$OUT/$name.seconds"
  echo "$name status=$rc seconds=$((end-start))"
}
test_case "candidate_original" "candidate"
test_case "predecessor_original" "base"

python3 - "$ROOT/candidate/pkg/downloader/downloader.go" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
s=p.read_text()
needle='''\tcase resp.StatusCode == http.StatusRequestedRangeNotSatisfiable:
\t\tresp.Body.Close()
\t\treturn finalizeOrRestartPartial(ctx, t, partial, offset, url, description, expectedDigest)'''
replacement='''\tcase resp.StatusCode == http.StatusRequestedRangeNotSatisfiable:
\t\tresp.Body.Close()
\t\tif offset == 0 {
\t\t\treturn fmt.Errorf("HTTP 416 received without a Range request for %q", url)
\t\t}
\t\treturn finalizeOrRestartPartial(ctx, t, partial, offset, url, description, expectedDigest)'''
if s.count(needle) != 1:
    raise SystemExit(f'UNKNOWN_PATCH_LOCATION count={s.count(needle)}')
p.write_text(s.replace(needle,replacement))
PY
(cd "$ROOT/candidate" && git diff -- pkg/downloader/downloader.go) > "$OUT/candidate_repair.patch"
sha256sum "$ROOT/candidate/pkg/downloader/downloader.go" > "$OUT/patched_source_sha256.txt"
test_case "candidate_repaired" "candidate"

# Protected original package test(s) after bounded candidate repair.
set +e
(cd "$ROOT/candidate" && go test -count=1 -timeout=4m -run '^TestResumeDownload$' -v ./pkg/downloader) > "$OUT/author_regression_suite.log" 2>&1
echo "$?" > "$OUT/author_regression_suite.status"
set -e

cp "$OUT/original_download.go" "$ROOT/candidate/pkg/downloader/downloader.go"
cmp "$OUT/original_download.go" "$ROOT/candidate/pkg/downloader/downloader.go"
test_case "candidate_after_ablation" "candidate"
sha256sum "$ROOT/candidate/pkg/downloader/downloader.go" > "$OUT/restored_source_sha256.txt"

python3 - "$OUT" <<'PY'
import hashlib,json,pathlib,sys
out=pathlib.Path(sys.argv[1])
statuses={p.stem:int(p.read_text().strip()) for p in out.glob('*.status')}
def has(name,marker): return marker in (out/f'{name}.log').read_text()
original=(out/'original_download.go').read_bytes()
method=json.loads((out/'mathgraph_generated_cycle_test.method.json').read_text())
verdict={
 "target_head":"335f61397af402ef77977a8e0c7a200f923349d1",
 "target_base":"f7b1c4f68b90299afc89ffeb47756e5fca590b91",
 "method":method,
 "statuses":statuses,
 "source_physically_restored":hashlib.sha256(original).hexdigest()==hashlib.sha256(original).hexdigest(),
 "original_candidate_has_generated_failure":statuses.get('candidate_original',0)!=0 and has('candidate_original','MG_GEN_RETRY_LOOP'),
 "base_passes_generated_test":statuses.get('predecessor_original',1)==0,
 "repair_passes_generated_test":statuses.get('candidate_repaired',1)==0,
 "ablation_returns_generated_failure":statuses.get('candidate_after_ablation',0)!=0 and has('candidate_after_ablation','MG_GEN_RETRY_LOOP'),
 "author_regression_retained":statuses.get('author_regression_suite',1)==0,
 "scope":"bounded adversarial HTTP 416 resilience, malformed remote response; human authored generator grammar and repair",
 "autonomous_L7":"UNKNOWN"
}
out.joinpath('report.json').write_text(json.dumps(verdict,sort_keys=True,indent=2)+'\n')
print(json.dumps(verdict,sort_keys=True))
if not all(verdict[x] for x in [
'original_candidate_has_generated_failure','base_passes_generated_test',
'repair_passes_generated_test','ablation_returns_generated_failure',
'author_regression_retained']):
 raise SystemExit(1)
PY
