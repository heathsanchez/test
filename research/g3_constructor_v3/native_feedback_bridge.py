"""V3 RED stub: no feedback repair; retains sealed V2 native behavior."""

import argparse
import json
from pathlib import Path
import sys

V2 = Path(__file__).resolve().parents[1] / "g3_constructor_v2"
sys.path.insert(0, str(V2))
from native_constructor_bridge import create  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--sha", required=True)
    args = ap.parse_args()
    create(json.loads(Path(args.manifest).read_text()), args.module, args.sha, Path(args.source_dir))


if __name__ == "__main__":
    main()
