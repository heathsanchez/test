#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir=${1:-"$root/evidence/runs/callgrind-g11-sealed"}

if ! command -v valgrind >/dev/null 2>&1; then
  echo "valgrind is required for Callgrind measurement" >&2
  exit 127
fi

mkdir -p "$output_dir"
cargo build --release --locked --manifest-path "$root/Cargo.toml"

for residual in G9-001 G10-001 G11-001; do
  fixture="$root/evidence/residuals/$residual/fixture.ndjson"
  valgrind \
    --tool=callgrind \
    --cache-sim=no \
    --branch-sim=no \
    --collect-jumps=no \
    --callgrind-out-file="$output_dir/$residual.callgrind" \
    "$root/target/release/metatron-kernel" < "$fixture"
done

echo "Callgrind cohort written to $output_dir"
