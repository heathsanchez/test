#!/usr/bin/env python3
# V24 intentionally reuses the frozen V23/V21 evaluator unchanged on a new corpus.
# The workflow stages only predeclared Mathlib module exports under arena-tests/good/.
from pathlib import Path
import shutil, subprocess, sys, json
root=Path.cwd()
# Run the exact frozen direct evaluator from V23 on the staged module corpus.
cp=subprocess.run([sys.executable,'scripts/run_developmental_distinction_external_gold_v23_direct.py'])
# Mirror the result into a V24-named directory for lineage clarity.
src=root/'results/developmental-distinction-external-gold-v23'
dst=root/'results/developmental-distinction-mathlib-gold-v24'
dst.mkdir(parents=True,exist_ok=True)
if src.exists():
    for p in src.iterdir():
        if p.is_file(): shutil.copy2(p,dst/p.name)
# Preserve V23 evaluator exit semantics.
raise SystemExit(cp.returncode)
