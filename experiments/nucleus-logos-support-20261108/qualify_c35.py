"""Run the unchanged 403-case qualification in one exact C35 diagnostic mode.

This imports the canonical qualifier rather than reimplementing any expected
verdict logic. All original proof inputs, reference binary and standard
global judgment allowance are unchanged.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("plain", "combined"))
    mode = p.parse_args().mode
    script = Path("experiments/nucleus-logos-support-20261108/qualify_projection.py").resolve()
    spec = importlib.util.spec_from_file_location("nucleus_c35_canonical_qualifier", script)
    if spec is None or spec.loader is None:
        raise ValueError("canonical protected qualifier missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if len(module.FLAGS) != 24 or set(module.FLAGS.values()) != {"1"}:
        raise ValueError("canonical qualification flags changed")
    if any(key.startswith("NUCLEUS_") for key in module.ENV):
        raise ValueError("protected qualifier unexpectedly inherited a diagnostic")
    module.ENV["NUCLEUS_DIAGNOSTIC_C35_ACTUAL_RECURSOR_CHARGE"] = "1"
    if mode == "combined":
        module.ENV["NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE"] = "1"
        module.ENV["NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT"] = "2048"
        module.ENV["NUCLEUS_DIAGNOSTIC_C34_FALLBACK_RESERVE_DIVISOR"] = "2"
        module.C28_FLAG_ON = True
    module.main()


if __name__ == "__main__":
    main()
