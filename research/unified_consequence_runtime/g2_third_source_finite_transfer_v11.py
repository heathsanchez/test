#!/usr/bin/env python3
"""V1.1 apparatus-only native rerun of the unchanged V1 frozen third-source method.

The sole seam lets the old V1 controller admit original head-author NEW tests,
which have no BASE test blob. Candidate source roles, grammar, method bytes,
finite join/causality checks and fully informed ledger remain frozen.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

from . import g2_third_source_finite_transfer_v1 as original
from . import g2_third_source_added_author_v11 as added

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
FREEZE="1be63843d095c636c6da6057f3b5442087601fb1"
AMENDMENT=U+"G2_THIRD_SOURCE_V11_TEST_ADMISSION_APPARATUS_FREEZE.json"


def main(out):
    raw=(ROOT/AMENDMENT).read_bytes()
    if raw!=subprocess.check_output(["git","-C",str(ROOT),"show",
                                     FREEZE+":"+AMENDMENT],timeout=45):
        raise ValueError("UNKNOWN_ORIGINAL_V11_APPARATUS_AMENDMENT_CHANGED")
    s=json.loads(raw)
    if s["original_science_prequery"]!=original.FROZEN_COMMIT or (
         s["method_state"]!="PRIMITIVE_AND_COMPOSITION_STILL_PINNED_EXACT_ORIGINAL_COMMIT_BYTES"):
        raise ValueError("UNKNOWN_V11_APPARATUS_DOES_NOT_PRESERVE_SCIENCE")
    result=original.main(out,admission_one=added.one)
    return result


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.unified_consequence_runtime.g2_third_source_finite_transfer_v11 FRESH_OUTPUT")
    main(Path(sys.argv[1]))
