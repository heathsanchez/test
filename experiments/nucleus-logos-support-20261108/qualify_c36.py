"""Run the canonical 403-case protected qualifier with C36 explicitly enabled."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grant", type=int, required=True,
                        choices=(512, 2048, 8192, 32768, 131072))
    grant = parser.parse_args().grant
    script = Path("experiments/nucleus-logos-support-20261108/qualify_projection.py").resolve()
    spec = importlib.util.spec_from_file_location("nucleus_c36_canonical_qualifier", script)
    if spec is None or spec.loader is None:
        raise ValueError("canonical protected qualifier is missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if len(module.FLAGS) != 24 or set(module.FLAGS.values()) != {"1"}:
        raise ValueError("canonical 24-flag selection changed")
    if any(key.startswith("NUCLEUS_") for key in module.ENV):
        raise ValueError("canonical qualifier unexpectedly inherited a diagnostic")
    module.ENV["NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_REPLAY"] = "1"
    module.ENV["NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_GRANT"] = str(grant)
    module.main()


if __name__ == "__main__":
    main()
