#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -f Kernel.olean Completeness.olean Core.olean
lean -o Kernel.olean Kernel.lean
LEAN_PATH=. lean -o Completeness.olean Completeness.lean
LEAN_PATH=. lean -o Core.olean Core.lean
LEAN_PATH=. lean Smoke.lean
