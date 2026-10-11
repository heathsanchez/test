# Collatz V190: odd-core inverse renewal and the zero-defect bottleneck

**Scope:** conditional exact analytic bridge between ROS V168 and V189; local bounded arithmetic checks; global Collatz **UNKNOWN**. No new Lean proof has yet checked the combined infinite-sum theorem.

## 1. One odd-core population, not two redundant ledgers

Let `T(n)=n/2` if `n` is even, `T(n)=(3n+1)/2` if odd. Assume for contradiction a nonempty terminal-disconnected saturated class `B` with `1_B(n)=1_B(T(n))`. Its least source `m>=15` is odd. Since `2n∈B iff n∈B`, write `O` for the odd members and `W_j(s)=Σ_{a∈O,a≡j(mod3)} a^{-s}`; `W=W_0+W_1+W_2`. The V168 full-population residue-2 share is exactly

    R_s(B)=(q W_1+W_2)/((1+q)W),   q=2^{-s}.

The accelerated odd map is `A(a)=(3a+1)/2^k` with `k=v_2(3a+1)>=1`. Every inverse odd arrow is

    a=(2^k y-1)/3, y odd, 3∤y,
    k even >=2 if y≡1(mod3); k odd >=1 if y≡2(mod3).

`a∈O iff A(a)∈O`. Therefore with `C_1=3^s q^2/(1-q^2)`, `C_2=3^s q/(1-q^2)`,

    W=C_1 W_1+C_2 W_2+Δ_s,
    Δ_s=Σ_{y∈O,3∤y} Σ_{k admissible}
        (3/(2^k y))^s * [(1-1/(2^k y))^{-s}-1] >0.

This is an exact identity, not a new strict anti-replenishment law. For `s=2`: `W_0+(2/5)W_1-(7/5)W_2=Δ_2`.

## 2. The critical V189 connection

Along a genuine inverse odd arrow, the shortcut takes exactly `k` real clocks from `a` to `y`. The V189 quantity `D(a,k)=3^k(a+1)-2^k(y+1)` satisfies

    D(a,k)=0 iff k=1; D(a,k)>0 for k>=2.

Thus the entire first odd inverse branch from `y≡2(mod3)` is defect-zero: `a=(2y-1)/3<y`, `T(a)=y`. **Defect-only penalization cannot suppress this replenishment.**

## 3. Exact conditional mass lower bound

Let `Z` be the `s=2` mass of odd sources in `O` whose first accelerated odd transition has `k=1`; let `P=W-Z` be the mass from `k>=2` sources. V168 with `m>=15` gives

    R_2(B)>= (1/3)*(29/30)^2=841/2700.
    W_2/W >= (5 R_2(B)-1)/3 >= 301/1620.

The `k>=2` inverse branch sums, preserving original heights and actual `+1`, satisfy

    P <= A_1 W_1+A_2 W_2,
    A_1=(3/5)*(4m/(4m-1))^2 <= 2160/3481,
    A_2=(3/20)*(8m/(8m-1))^2 <= 2160/14161.

Since `W_1<=W-W_2` and `A_1>A_2`,

    Z/W >= 1-(2160/3481)*(1-301/1620)
             -(2160/14161)*(301/1620)
        = 3284703/7042063 > 46.64%.

**Meaning:** if a terminal-disconnected saturated class exists, more than 46.64% of its weighted odd-core mass must start with defect-zero `k=1` branches. This is a conditional necessity, not a contradiction or an existence theorem.

## 4. Independent arithmetic relaxation remains feasible

For every integer `m>=15`, abstract normalized mass values

    W_0=1/10,
    W_1=29/45+5/(36m),
    W_2=23/90-5/(36m)

satisfy the coarse `s=2` renewal equation with positive correction `1/(4m)` and V168's necessary residue bounds. These numbers are *not* a set of natural sources and do *not* establish a bad class. They demonstrate that the **scalar population constraints alone are algebraically consistent**.

## 5. Evidence and residual

- [V168 exact/negative control checkpoint](https://github.com/heathsanchez/test/commit/d2998a3ca633b80002ba3176d42293ef66081564).
- [V189 exact Lean defect ledger](https://github.com/heathsanchez/test/blob/8dbff92091d71837d28034171c93dc6c303783ef/formal/Collatz/InverseHeightDefectLedger.lean) and [green V189 CI](https://github.com/heathsanchez/test/actions/runs/38109758765).
- [V190 exact Python controls](research/collatz_v190_odd_core_bridge.py): 5,000 original odd sources; 500 rational source-transfer terms; 84 protected higher-target endpoints; exact 46.64% rational arithmetic; G5/G7 negative controls; aggregate algebraic feasibility checks.
- **WARRANTED:** elementary odd-core identities, plus exact bounded executable checks at the stated boundary.
- **NOT YET LEAN-QUALIFIED:** the new infinite weighted-sum conditional 46.64% theorem.
- **REJECTED:** defect-by-itself forces class deficit; aggregates alone imply contradiction.
- **UNKNOWN:** all-scale source-conditioned *cross-generation* bound coupling `k=1` to later `k>=2`, and Collatz convergence.

**Next smallest consequential experiment:** condition on a zero-defect `k=1` branch, preserve its original source and real clock, and derive/test whether a later independent `k>=2` event necessarily creates a net loss of odd-core weighted mass. Compare the true `+1` arithmetic against intercept-5/-7 negative controls. No circular eventual-descent premise.
