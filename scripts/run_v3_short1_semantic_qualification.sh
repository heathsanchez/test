#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
OUT="$GITHUB_WORKSPACE/v3-short1-semantic"
rm -rf "$OUT" /tmp/mgv3-src /tmp/mgv3-baseline /tmp/mgv3-short1 /tmp/arena-v3s-sem
mkdir -p "$OUT"

git clone --quiet https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/mgv3-src
cd /tmp/mgv3-src
git checkout --quiet "$V2"
git worktree add /tmp/mgv3-baseline "$V2"
git worktree add /tmp/mgv3-short1 "$V2"

python3 - <<'PY'
from pathlib import Path
p=Path('/tmp/mgv3-short1/src/conv.rs')
s=p.read_text()
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
new='''                    } else {\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let a = lx.min(ly);\n                        let b = lx.max(ly);\n                        if a == 1 && (b == 3 || b == 4 || b == 6) {\n                            if lx < ly {\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }\n                            } else if ly < lx {\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }\n                            }\n                        }\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
anchor='''                    } else if rh.is_lt(&lh) {'''
pos=s.index(anchor)
target=s.index(old,pos)
s=s[:target]+s[target:].replace(old,new,1)
p.write_text(s)
assert 'a == 1 && (b == 3 || b == 4 || b == 6)' in s
PY

for arm in baseline short1; do
  cd "/tmp/mgv3-$arm"
  cargo test --release --locked
  RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
  cp target/release/sokonanoda "/tmp/mgv3-bin-$arm"
done

cat >/tmp/checker-v3s-sem.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3s-sem
cd /tmp/arena-v3s-sem
nix develop -c ./lka.py build-test

: > "$OUT/semantic-gate.txt"
count=0
mismatch=0
while IFS= read -r f; do
  count=$((count+1))
  bstatus=0; cstatus=0
  timeout 180 /tmp/mgv3-bin-baseline /tmp/checker-v3s-sem.json < "$f" >/tmp/v3s-base.out 2>/tmp/v3s-base.err || bstatus=$?
  timeout 180 /tmp/mgv3-bin-short1 /tmp/checker-v3s-sem.json < "$f" >/tmp/v3s-short1.out 2>/tmp/v3s-short1.err || cstatus=$?
  if [ "$bstatus" -ne "$cstatus" ]; then
    mismatch=$((mismatch+1))
    printf 'MISMATCH\t%s\tbase=%s\tshort1=%s\n' "$f" "$bstatus" "$cstatus" | tee -a "$OUT/semantic-gate.txt"
  else
    printf 'MATCH\t%s\tstatus=%s\n' "$f" "$bstatus" >> "$OUT/semantic-gate.txt"
  fi
done < <(find _build/tests -type f -name '*.ndjson' | sort)

printf 'tests=%s\nmismatches=%s\ncandidate=literal_short1_1346\n' "$count" "$mismatch" | tee "$OUT/decision.txt"
if [ "$mismatch" -eq 0 ]; then
  echo 'V3_SEMANTIC_DECISION=QUALIFIED' | tee -a "$OUT/decision.txt"
  echo "RECURSIVE_SEMANTIC_GATE_PASS tests=$count candidate=literal_short1_1346" | tee -a "$OUT/semantic-gate.txt"
else
  echo 'V3_SEMANTIC_DECISION=MISMATCH' | tee -a "$OUT/decision.txt"
  exit 1
fi
