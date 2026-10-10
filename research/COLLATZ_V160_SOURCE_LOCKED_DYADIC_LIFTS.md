# Collatz V160 — real future-class lifts and the certificate-height separator

**Research status:** actual affine lift is an unconditional Lean target; source-attached two-clock ancestor construction is Lean-conditional on an explicit *number-theory* power-congruence witness. The primitive-root lemma below has an elementary all-exponents proof in this note, and a bounded independent exact test, but is **not kernel-rebuilt in V160**. Collatz is UNKNOWN, not QED.

## 1. Exact parity-cylinder law — no convergence assumption

Define the actual shortcut as T(n)=n/2 for even n and T(n)=(3n+1)/2 for odd n. Let a(n,k) count actual odd inputs among the first k shortcut steps.

For **every** n,k,q in Nat,

    T^k(n+2^k*q)=T^k(n)+3^a(n,k)*q.

Proof by induction on k. At k=0 it is the identity. If the k-step lift is x+2z, the genuine one-step identity is

    T(x+2z)=T(x)+(if x even then z else 3z),

which increments the actual odd-count exponent exactly in the second case. The source n+2^k*q is genuine and has the same first k parity choices as n.

This source-typed lemma is **stronger than a finite parity-word picture** and is independent of Collatz's global outcome.

## 2. Powers of 2 enumerate units modulo powers of 3

For a>=1 set E_a=2*3^(a-1). We prove by induction

    2^E_a ≡ 1+3^a (mod 3^(a+1)).

At a=1, 2^2=4. For the induction, write 2^E_a=1+3^a(1+3h). Cubing to obtain 2^E_(a+1), use

    (1+u)^3=1+3u+3u²+u³,  u=3^a(1+3h).

The u² and u³ contributions are divisible by 3^(a+2), because a>=1. Hence the required congruence at a+1.

The multiplicative order of 2 modulo 3 starts at 2=E_1. If it equals E_a modulo 3^a, the order modulo 3^(a+1) is a multiple of E_a. Our congruence shows it is **not** E_a but divides 3E_a (its cube is 1 modulo 3^(a+1)). Therefore it is exactly 3E_a=E_(a+1).

Exactly 2*3^(a-1) residues modulo 3^a are coprime to 3. Since powers of 2 have that order, **they enumerate every such residue**. This elementary number-theory result concerns units modulo 3^a, not the Collatz conjecture.

For a=0 the modulus is 1 and every residue condition is vacuous.

## 3. Genuine ancestors in every dyadic cylinder of every future class

Choose any positive target b. First replace it, if necessary, by b'=T^h(b) with 3∤b': such an h exists unconditionally by the V158 all-depth ternary sieve, taking 2^h>b.

Take any bit depth k and source residue 0<=r<2^k. Let a=a(r,k) and g=T^k(r). If r>0, V158 gives 3∤g; if r=0, a=g=0.

When r>0, by the primitive-root lemma, for arbitrarily large L,

    2^L*b' ≡ g (mod 3^a).

Choose L large enough that 2^L*b'>=g, and define

    q=(2^L*b'-g)/3^a,       n=r+2^k*q.

Then n is a genuine positive integer, n≡r (mod2^k), and the all-depth affine law gives

    T^k(n)=2^L*b',   T^(k+L)(n)=b'.

Thus **for every future-coalescence class and every dyadic residue class, there exist infinitely many actual positive members**. These are genuine joins at real clocks, not 2-adic ghost sources. This unconditional mathematical conclusion uses the elementary number theory above; the V160 Lean file formalizes the exact source-typed constructor while taking the congruence solution as an explicit premise.

**This does not imply that distinct future classes intersect.** Distinct subsets can both be dense in the dyadic/profinite topology.

## 4. Mersenne all-ones adversarial certificate height

Take k>=1 and r=2^k-1. The first k actual steps are odd, with

    T^j(r)=2^(k-j)*3^j-1,   0<=j<=k.

Thus a=k and g=3^k-1. The very specific certificate requiring T^k(n)=2^L has the modular condition

    2^L ≡ -1 (mod 3^k).

The primitive-root lemma proves 2 has order 2*3^(k-1) modulo 3^k. The element 2^(3^(k-1)) has order 2, and modulo an odd prime power the only order-2 unit is -1: 3^k divides (x-1)(x+1) only by dividing one of them, since their difference is 2. Consequently

    L ≡ 3^(k-1) (mod 2*3^(k-1)),

and the **least** valid nonnegative exponent is L=3^(k-1). It already exceeds the endpoint-size threshold. The chosen source n=r+2^k*((2^L-g)/3^k) therefore has exponentially many bits in k.

This does **not** bound the shortest eventual terminal clock of r itself or the shorter two-clock merger certificates from V119. It is an exact lower bound for this **restricted, direct kth-endpoint-to-power-of-two proof grammar** only.

## 5. Why this does not yield V151 density-one coverage

For fixed prefix r, depth k, and target b', the constructed sources are indexed by powers L in a single arithmetic progression modulo E_a. If n_L<X, their target endpoint 2^L*b' is at most g+3^a*(X-r)/2^k, so L is O(log X). There are only **O(log X)** such direct-power certificates in that fixed residue cylinder below X.

That is infinite topological coverage but zero natural-density coverage for this direct certificate grammar. It cannot supply V151's unbounded *density-one terminal-certificate mass* premise.

The genuinely new target is therefore NOT another existence argument. It is a source-attached abundance/height estimate on **all independently verified future mergers**, including chart overlap and reuse, strong enough to force sparse unresolved population along unbounded natural cutoffs. There is no such universal theorem currently verified.

## Evidence and protected status

The Python audit tests complete dyadic residue families for k=1..9 and eight 3-coprime targets, plus all-source affine shifts, the primitive-root orbit through exponent a=9, and the Mersenne exponential-height control. Lean checks the affine source lift, positivity/residue protection and real two-clock join conditional on supplied congruence witness. The mathematical primitive-root lemma is an elementary proof in this note, NOT an independently compiled Lean declaration. All statuses retain **GLOBAL COLLATZ UNKNOWN — NO QED**.
