#!/usr/bin/env python3
from pathlib import Path
import argparse,re

ROOT=Path(__file__).resolve().parent
BASE=(ROOT/"Submission_v27.lean").read_text()

VARIANTS={
"xor_triple": r"""def bstep (m : Nat) : Nat :=
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  ((m ||| r) ^^^ (l &&& m &&& r)) &&& M
""",
"xor_or_cnotl": r"""def bstep (m : Nat) : Nat :=
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  ((r ^^^ m) ||| (m &&& (M ^^^ l))) &&& M
""",
"xor_or_rnotl": r"""def bstep (m : Nat) : Nat :=
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  ((r ^^^ m) ||| (r &&& (M ^^^ l))) &&& M
""",
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("variant",choices=sorted(VARIANTS))
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    pat=r"def bstep \(m : Nat\) : Nat :=\n.*?(?=\ndef biter :)"
    out,n=re.subn(pat,VARIANTS[args.variant].rstrip()+"\n",BASE,count=1,flags=re.S)
    if n!=1: raise SystemExit(f"replacement count {n}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(out)
    print(args.variant,args.output,len(out))
if __name__=="__main__":
    main()
