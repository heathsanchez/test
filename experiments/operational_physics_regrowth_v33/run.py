#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from core import run_all


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='evidence.json')
    ns = ap.parse_args()
    result = run_all()
    result['source_hashes'] = {
        'core.py': hashlib.sha256(Path(__file__).with_name('core.py').read_bytes()).hexdigest(),
        'test_regrowth.py': hashlib.sha256(Path(__file__).with_name('test_regrowth.py').read_bytes()).hexdigest(),
    }
    Path(ns.out).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['verdict'].startswith('PASS_') else 1

if __name__ == '__main__':
    raise SystemExit(main())
