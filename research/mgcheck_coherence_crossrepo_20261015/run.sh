#!/usr/bin/env bash
set -euo pipefail
ROOT="$(pwd)"
DIR="$ROOT/research/mgcheck_coherence_crossrepo_20261015"
E="$DIR/evidence"
mkdir -p "$E" "$ROOT/workspaces"
clone_at_sha() {
  local repo="$1" sha="$2" out="$3"
  mkdir -p "$out"
  git -C "$out" init -q
  git -C "$out" remote add origin "https://github.com/$repo.git"
  git -C "$out" -c protocol.version=2 fetch -q --depth=1 origin "$sha"
  git -C "$out" checkout -q --detach "$sha"
  test "$(git -C "$out" rev-parse HEAD)" = "$sha"
}
clone_at_sha "uiri/toml" "1cc59b351e1ff5c7591ab05d4d027638100af82b" "$ROOT/workspaces/b_base"
clone_at_sha "uiri/toml" "5be7c5041f28df68365ec4f3d77b3363ede198be" "$ROOT/workspaces/b_head"
clone_at_sha "avakar/pytoml" "d883c7cf2ae48eae5ba572c1d45bc46fbf8e5cb5" "$ROOT/workspaces/c_base"
clone_at_sha "avakar/pytoml" "b28b705bd364aa7d7fbc9f6102bca3ceda223dbf" "$ROOT/workspaces/c_head"
python3 -m compileall -q "$ROOT/workspaces/b_base" "$ROOT/workspaces/b_head" "$ROOT/workspaces/c_base" "$ROOT/workspaces/c_head"
printf '2407927cfc0a7b5061aefecce70ae69ddd19a70820883d08439da5fb2aa363d1  %s\n' "$DIR/acquired_capability_A_from_original_archive.json" | sha256sum -c
for rev in base head; do
  for family in b c; do
    python3 "$DIR/native_bridge.py" "$ROOT/workspaces/$family"_"$rev" "$family" "$rev" "$E" | tee "$E/$family"_"$rev".stdout
  done
done
python3 - "$ROOT/workspaces" "$E" <<'PY'
import hashlib, json, pathlib, shutil, sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
for family in ('b','c'):
    b=root/(family+'_base');h=root/(family+'_head')
    before={}
    changed=[]
    for p in h.rglob('*.py'):
        rel=p.relative_to(h)
        if 'test' in '/'.join(rel.parts).lower(): continue
        if not (b/rel).is_file(): continue
        if p.read_bytes()!=(b/rel).read_bytes():
            before[str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
            p.write_bytes((b/rel).read_bytes())
            changed.append(str(rel))
    if not changed: raise SystemExit('UNKNOWN_NO_SOURCE_ABLATION '+family)
    (out/(family+'_ablation_source.json')).write_text(json.dumps({'production_files':changed,'original_head_blob_digests':before},sort_keys=True,indent=2))
    print('PHYSICAL_ABLATION',family,changed)
PY
for family in b c; do
  python3 "$DIR/native_bridge.py" "$ROOT/workspaces/$family"_head "$family" ablated "$E" | tee "$E/$family"_ablated.stdout
done
python3 "$DIR/admit.py" "$E"
