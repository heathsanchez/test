#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

runpy.run_path(str(ROOT / "packed_core_v4.py"))
src = (OUT / "Submission_v4.lean").read_text()
start = src.index("def packedStep")
prefix = src[:start]

K = [
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
]

lines = []
lines.append("/-- Straight-line one-block SHA-256.  The trusted list schedule and Digest")
lines.append("    round recursion are compiled into scalar Nat lets, so target reduction")
lines.append("    never materialises the 64-element schedule or 64 intermediate structures. -/")
lines.append("def sha256stepStraight (d : Digest) : Digest :=")
seed_words = ["d.a","d.b","d.c","d.d","d.e","d.f","d.g","d.h",
              "0x80000000","0","0","0","0","0","0","256"]
for i,w in enumerate(seed_words):
    lines.append(f"  let w{i} := {w}")
for t in range(16,64):
    lines.append(
        f"  let w{t} := add32 (add32 (smallSigma1 w{t-2}) w{t-7}) "
        f"(add32 (smallSigma0 w{t-15}) w{t-16})")
for name in "abcdefgh":
    lines.append(f"  let {name}0 := iv.{name}")
for t,k in enumerate(K):
    lines.append(
        f"  let t1_{t} := add32 h{t} "
        f"(add32 (bigSigma1 e{t}) (add32 (ch e{t} f{t} g{t}) "
        f"(add32 0x{k:08x} w{t})))")
    lines.append(
        f"  let t2_{t} := add32 (bigSigma0 a{t}) (maj a{t} b{t} c{t})")
    lines.append(f"  let a{t+1} := add32 t1_{t} t2_{t}")
    lines.append(f"  let b{t+1} := a{t}")
    lines.append(f"  let c{t+1} := b{t}")
    lines.append(f"  let d{t+1} := c{t}")
    lines.append(f"  let e{t+1} := add32 d{t} t1_{t}")
    lines.append(f"  let f{t+1} := e{t}")
    lines.append(f"  let g{t+1} := f{t}")
    lines.append(f"  let h{t+1} := g{t}")
lines.append("  ⟨add32 iv.a a64, add32 iv.b b64, add32 iv.c c64, add32 iv.d d64,")
lines.append("   add32 iv.e e64, add32 iv.f f64, add32 iv.g g64, add32 iv.h h64⟩")
straight = "\n".join(lines) + "\n\n"

middle = straight + r'''
/--
The straight-line transition is definitionally the same 64-round computation
as the trusted list/structure specification.  This is paid once at source
qualification; future chain steps reuse the theorem as an opaque capability.
-/
theorem sha256stepStraight_eq (d : Digest) :
    sha256stepStraight d = sha256step d := by
  rfl

theorem valid_sha256stepStraight (d : Digest) :
    ValidDigest (sha256stepStraight d) := by
  rw [sha256stepStraight_eq]
  exact valid_sha256step d

def packedStepStraight (x : Nat) : Nat :=
  packDigestLE (sha256stepStraight (unpackDigestLE x))

def iterFn {α : Type} (f : α → α) : Nat → α → α
  | 0, x => x
  | t + 1, x => iterFn f t (f x)

/-- Generic transition conjugacy: prove one step once, iterate cheaply. -/
theorem conjugate_iter
    {α β : Type}
    (pack : α → β) (unpack : β → α) (step : α → α) (P : α → Prop)
    (hleft : ∀ a, P a → unpack (pack a) = a)
    (hstep : ∀ a, P a → P (step a)) :
    ∀ t a, P a →
      unpack (iterFn (fun x => pack (step (unpack x))) t (pack a)) =
        iterFn step t a
  | 0, a, ha => hleft a ha
  | t + 1, a, ha => by
      simp only [iterFn]
      rw [hleft a ha]
      exact conjugate_iter pack unpack step P hleft hstep
        t (step a) (hstep a ha)

theorem iterFn_eq_iterDigest (step : Digest → Digest) :
    ∀ t d, iterFn step t d = iterDigest step t d
  | 0, d => rfl
  | t + 1, d => by
      simp only [iterFn, iterDigest]
      exact iterFn_eq_iterDigest step t (step d)

/-- Reuse the certified one-step equality without reopening the 64-round body. -/
theorem iterDigest_straight_eq :
    ∀ t d, iterDigest sha256stepStraight t d =
      iterDigest sha256step t d
  | 0, d => rfl
  | t + 1, d => by
      simp only [iterDigest]
      rw [sha256stepStraight_eq]
      exact iterDigest_straight_eq t (sha256step d)

def impl (n : Nat) : Nat :=
  let d0 := seedDigest (sha256Seed n)
  let packed := iterFn packedStepStraight (sha256Steps n) (packDigestLE d0)
  encodeDigest (unpackDigestLE packed)

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  change
    encodeDigest
      (unpackDigestLE
        (iterFn
          (fun x => packDigestLE
            (sha256stepStraight (unpackDigestLE x)))
          (sha256Steps n) (packDigestLE (seedDigest (sha256Seed n))))) =
      encodeDigest
        (iterDigest sha256step (sha256Steps n) (seedDigest (sha256Seed n)))
  rw [conjugate_iter
      packDigestLE unpackDigestLE sha256stepStraight ValidDigest
      unpack_pack (fun a _ => valid_sha256stepStraight a)
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n))]
  rw [iterFn_eq_iterDigest]
  rw [iterDigest_straight_eq]

end Submission
'''

text = prefix + middle
p = OUT / "Submission_v6.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
