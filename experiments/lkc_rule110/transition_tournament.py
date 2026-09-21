#!/usr/bin/env python3
from pathlib import Path
import argparse, re

ROOT = Path(__file__).resolve().parent
BASE = (ROOT / "Submission_v27.lean").read_text()

VARIANTS = {
    "minxor": r"""def bstep (m : Nat) : Nat :=
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  (m ^^^ (r &&& (l ||| (M ^^^ m)))) &&& M
""",
    "share_r": r"""def bstep (m : Nat) : Nat :=
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  (M ^^^ (((M ^^^ m) &&& (M ^^^ r))
          ||| ((((m <<< 1) ||| (m >>> 255)) &&& M) &&& m &&& r))) &&& M
""",
    "share_lr": r"""def bstep (m : Nat) : Nat :=
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  (M ^^^ (((M ^^^ m) &&& (M ^^^ r)) ||| (l &&& m &&& r))) &&& M
""",
    "share_lrn": r"""def bstep (m : Nat) : Nat :=
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let nm := M ^^^ m
  let nr := M ^^^ r
  (M ^^^ ((nm &&& nr) ||| (l &&& m &&& r))) &&& M
""",
    "share_core": r"""def bstep (m : Nat) : Nat :=
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let a := (M ^^^ m) &&& (M ^^^ r)
  let b := l &&& m &&& r
  (M ^^^ (a ||| b)) &&& M
""",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=sorted(VARIANTS))
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    pattern = r"def bstep \(m : Nat\) : Nat :=\n.*?(?=\ndef biter :)"
    out, n = re.subn(pattern, VARIANTS[args.variant].rstrip() + "\n", BASE, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"expected exactly one bstep replacement, got {n}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out)
    print(f"generated {args.variant}: {args.output} ({len(out)} bytes)")

if __name__ == "__main__":
    main()
