from pathlib import Path
import json, re, shutil, subprocess

SRC = Path('full48/remaining20_promote_v1').resolve()
OUT = Path('full48_decontaminated_v1').resolve()
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(SRC, OUT)

ring = OUT/'Galoistools/Proof/Ring.lean'
div = OUT/'Galoistools/Proof/Division.lean'

MUL_HELPER = r'''  have mul_eval_hom (u v : List Nat) :
      Galoistools.refPolyEval p (Galoistools.gfMul u v p) x =
        (Galoistools.refPolyEval p u x * Galoistools.refPolyEval p v x) % p := by
    simp only [canonical, Galoistools.gfMul]
    by_cases hzero : u = [] ∨ v = []
    · rw [if_pos hzero]
      rcases hzero with rfl | rfl <;> simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux]
    · rw [if_neg hzero, refPolyEval_gfStrip]
      simp only [Galoistools.refPolyEval, List.reverse_reverse]
      have hconv := natModEq_refPolyEvalRevAux_convolve p x u.reverse v.reverse
      unfold NatModEq at hconv
      have hevalmod :
          Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) % p =
            Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) := by
        cases Galoistools.convolve p u.reverse v.reverse <;>
          simp [Galoistools.refPolyEvalRevAux]
      calc
        Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) =
            Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) % p := hevalmod.symm
        _ = (Galoistools.refPolyEvalRevAux p x u.reverse *
              Galoistools.refPolyEvalRevAux p x v.reverse) % p := hconv
'''

MONIC_HELPER = r'''  have monic_leadCoeff_one (xs : List Nat) (hne : xs ≠ [])
      (hcop : Nat.gcd (Galoistools.refLeadCoeff xs) p = 1) :
      Galoistools.refLeadCoeff (Galoistools.gfMonic xs p).2 = 1 := by
    have egcd_bezout : ∀ fuel a b,
        let r := Galoistools.egcdInt fuel a b
        a * r.2.1 + b * r.2.2 = r.1 := by
      intro fuel
      induction fuel with
      | zero =>
          intro a b
          simp [Galoistools.egcdInt]
      | succ fuel ih =>
          intro a b
          simp only [Galoistools.egcdInt]
          by_cases hb : b = 0
          · simp [hb]
          · simp only [hb, ↓reduceIte]
            let r := Galoistools.egcdInt fuel b (a % b)
            have hr := ih b (a % b)
            change a * r.2.2 + b * (r.2.1 - (a / b) * r.2.2) = r.1
            have halg :
                a * r.2.2 + b * (r.2.1 - (a / b) * r.2.2) =
                  b * r.2.1 + (a - b * (a / b)) * r.2.2 := by
              simp only [Int.sub_eq_add_neg, Int.mul_add, Int.add_mul,
                Int.mul_neg, Int.neg_mul, Int.mul_assoc]
              ac_rfl
            rw [halg, ← Int.emod_def]
            exact hr
    have egcd_gcd : ∀ fuel m n : Nat, n < fuel →
        (Galoistools.egcdInt fuel (Int.ofNat m) (Int.ofNat n)).1 =
          Int.ofNat (Nat.gcd m n) := by
      intro fuel
      induction fuel with
      | zero =>
          intro m n h
          exact (Nat.not_lt_zero n h).elim
      | succ fuel ih =>
          intro m n h
          by_cases hn : n = 0
          · subst n
            simp [Galoistools.egcdInt]
          · have hnpos : 0 < n := Nat.pos_of_ne_zero hn
            have hnfuel : n ≤ fuel := Nat.le_of_lt_succ h
            have hmod0 : m % n < n := Nat.mod_lt m hnpos
            have hmod : m % n < fuel := Std.lt_of_lt_of_le hmod0 hnfuel
            rw [Galoistools.egcdInt]
            have hnI : (Int.ofNat n) ≠ 0 := (Int.ofNat_ne_zero).2 hn
            rw [if_neg hnI]
            have hr := ih n (m % n) hmod
            change (Galoistools.egcdInt fuel (Int.ofNat n) (Int.ofNat (m % n))).1 =
              Int.ofNat (Nat.gcd m n)
            have hgcd : Nat.gcd m n = Nat.gcd n (m % n) := by
              rw [Nat.gcd_comm m n, Nat.gcd_rec n m, Nat.gcd_comm (m % n) n]
            rw [hgcd]
            exact hr
    cases xs with
    | nil => contradiction
    | cons a as =>
      simp only [Galoistools.refLeadCoeff] at hcop
      change Galoistools.refLeadCoeff (Galoistools.gfMonic (a :: as) p).2 = 1
      by_cases ha : a = 1
      · simp [Galoistools.gfMonic, ha, Galoistools.refLeadCoeff]
      · rw [Galoistools.gfMonic]
        simp only [ha, ↓reduceIte, Galoistools.gfQuoGround, List.map_cons,
          Galoistools.refLeadCoeff]
        unfold Galoistools.invMod
        let r := Galoistools.egcdInt (a + p + 1) (Int.ofNat (a % p)) (Int.ofNat p)
        have hbez := egcd_bezout (a + p + 1) (Int.ofNat (a % p)) (Int.ofNat p)
        have hfuel : p < a + p + 1 := by omega
        have hg := egcd_gcd (a + p + 1) (a % p) p hfuel
        have hgp : Nat.gcd (a % p) p = 1 := by
          rw [← Nat.gcd_rec p a, Nat.gcd_comm]
          exact hcop
        have hr1 : r.1 = 1 := by
          dsimp [r]
          simpa [hgp] using hg
        change Int.ofNat (a % p) * r.2.1 + Int.ofNat p * r.2.2 = r.1 at hbez
        rw [hr1] at hbez
        have hone : (1 : Int) % Int.ofNat p = 1 := by
          change Int.ofNat (1 % p) = Int.ofNat 1
          rw [Nat.mod_eq_of_lt hp1]
        have hmodI := congrArg (fun z : Int => z % Int.ofNat p) hbez
        change (Int.ofNat (a % p) * r.2.1 + Int.ofNat p * r.2.2) % Int.ofNat p =
          (1 : Int) % Int.ofNat p at hmodI
        rw [Int.add_mul_emod_self_left, hone] at hmodI
        have hcoef :
            (Int.ofNat (a % p) * (r.2.1 % Int.ofNat p)) % Int.ofNat p = 1 := by
          rw [← Int.emod_add_mul_ediv r.2.1 (Int.ofNat p)] at hmodI
          rw [Int.mul_add] at hmodI
          have hreassoc :
              Int.ofNat (a % p) * (Int.ofNat p * (r.2.1 / Int.ofNat p)) =
                Int.ofNat p * (Int.ofNat (a % p) * (r.2.1 / Int.ofNat p)) := by
            ac_rfl
          rw [hreassoc, Int.add_mul_emod_self_left] at hmodI
          exact hmodI
        have hp0 : p ≠ 0 := by omega
        have hpI0 : (Int.ofNat p) ≠ 0 := (Int.ofNat_ne_zero).2 hp0
        have hxnonneg : 0 ≤ r.2.1 % Int.ofNat p :=
          Int.emod_nonneg r.2.1 hpI0
        have hxcast :
            Int.ofNat ((r.2.1 % Int.ofNat p).toNat) = r.2.1 % Int.ofNat p := by
          exact Int.toNat_of_nonneg hxnonneg
        rw [← hxcast] at hcoef
        change Int.ofNat (((a % p) * (r.2.1 % Int.ofNat p).toNat) % p) = Int.ofNat 1 at hcoef
        have hnat : ((a % p) * (r.2.1 % Int.ofNat p).toNat) % p = 1 :=
          Int.ofNat.inj hcoef
        change a * ((r.2.1 % (Int.ofNat p)).toNat) % p = 1
        simpa [Nat.mul_mod] using hnat
'''

def block(src, name):
    start = re.search(rf'-- !benchmark @start proof def={re.escape(name)} kind=prove[^\n]*\n', src)
    if not start: raise RuntimeError(name)
    endmark = f'-- !benchmark @end proof def={name}'
    end = src.find(endmark, start.end())
    return start.end(), end

r = ring.read_text()
for name in ['prove_mul_comm_eval','prove_mul_assoc_eval','prove_mul_add_distrib_eval']:
    a,b = block(r,name)
    body = r[a:b]
    intro_line_end = body.find('\n') + 1
    body = body[:intro_line_end] + MUL_HELPER + body[intro_line_end:]
    body = body.replace('prove_mul_eval_hom', 'mul_eval_hom')
    r = r[:a] + body + r[b:]
ring.write_text(r)

d = div.read_text()
a,b = block(d,'prove_gcd_monic')
body = d[a:b]
needle = '  have monic_norm : ∀ xs : List Nat,\n'
pos = body.find(needle)
if pos < 0: raise RuntimeError('monic_norm anchor missing')
body = body[:pos] + MONIC_HELPER + body[pos:]
body = body.replace('exact prove_monic_leadCoeff_one xs p hp1 hne (norm_lead_coprime xs hn hne)',
                    'exact monic_leadCoeff_one xs hne (norm_lead_coprime xs hn hne)')
d = d[:a] + body + d[b:]
div.write_text(d)

# Audit benchmark blocks for unsafe tokens and direct cross-target references.
proof_files = sorted((OUT/'Galoistools'/'Proof').glob('*.lean'))
start_re = re.compile(r'-- !benchmark @start proof def=([A-Za-z0-9_]+) kind=prove[^\n]*\n')
entries=[]
for pf in proof_files:
    src=pf.read_text()
    for m in start_re.finditer(src):
        name=m.group(1); end=src.find(f'-- !benchmark @end proof def={name}',m.end())
        entries.append((pf,name,src[m.end():end]))
all_names={n for _,n,_ in entries}
violations=[]; cross=[]
for pf,name,body in entries:
    bad=[t for t in ('sorry','admit','axiom','unsafe') if re.search(rf'\b{t}\b',body.lower())]
    if bad: violations.append({'target':name,'tokens':bad})
    refs=sorted(o for o in all_names if o!=name and re.search(rf'\b{re.escape(o)}\b',body))
    if refs: cross.append({'target':name,'refs':refs})

subprocess.run(['lake','clean'],cwd=OUT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
cp=subprocess.run(['lake','build'],cwd=OUT,text=True,capture_output=True)
print((cp.stdout+'\n'+cp.stderr)[-12000:])
result={'proof_blocks':len(entries),'unsafe_violations':violations,'cross_target_references':cross,'clean_full_build_exit':cp.returncode}
Path('full48_decontaminate_result.json').write_text(json.dumps(result,indent=2,sort_keys=True))
print('FULL48_DECONTAMINATE_V1',json.dumps({'proof_blocks':len(entries),'unsafe_violations':len(violations),'cross_target_references':len(cross),'clean_full_build_exit':cp.returncode},sort_keys=True))
raise SystemExit(0 if cp.returncode==0 and not violations and not cross and len(entries)>=48 else 1)
