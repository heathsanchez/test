# Collatz deletion audit — 18 September 2026

Base commit: `628d7b63b4591324ea4ccfa3c99e25349dd2701d`. This checkpoint is an exact reduction audit, not a global Collatz proof or a new verification record. These are handwritten arguments with exact computational checks, not Lean formalizations. No original experiment is modified.

## Delete an independent slope obligation

For a genuine shortcut prefix beginning at b>1,

    2^m T^m(b) = 3^c b + E,  E >= 0.

Thus T^m(b)<b already implies 3^c<2^m. The separate coefficient test in `collatz_direct_zero_tail_big.cpp` is redundant after genuine boundary descent. Previous conversational claims of possible slope-wait cases were incorrect. Also, epsilon<b(1-rho), with rho=3^c/2^m and epsilon=E/2^m, is exactly T^m(b)<b rewritten; it is not itself a new bound or rank.

Zero-tail refinement must preserve its domain: the correct lifted family after t further zero bits is n=2^(k+t)u+b, not n=2^k u+b. For example T^4(3)=2 but T^4(7)=13; the certified extension is T^4(3+16u)=2+9u.

## Sharp envelope and prefix conditioning

If the FIRST coefficient contraction uses Q odd steps, its length is L=bit_length(3^Q). Before the j-th odd step, at zero-based position p_j, coefficient survival forces

    2^p_j <= 3^(j-1).

Hence the additive numerator satisfies the sharp bound

    E <= H_Q = sum_j 3^(Q-j) 2^floor(log2(3^(j-1))).

The latest allowed odd positions attain the bound. Exact computation needs no logarithms:

    H_0=0;
    H_(q+1)=3 H_q+2^(bit_length(3^q)-1).

For a known pre-crossing prefix with c odd steps and numerator E_k, a sharper conditional bound is

    E_final <= H_Q-3^(Q-c)(H_c-E_k).

The known contribution scales by 3^(Q-c); only the remaining terms are maximized. At an odd step at position k before first contraction, C=H_c-E_k obeys

    C_new = 3C + 2^floor(log2(3^c))-2^k >= 3C.

So C/3^c never decreases before first contraction. This is accumulated deviation from the worst-case word, not a global termination rank.

Do not discard source compatibility. A word with numerator E and odd count Q is executable only on its source class

    b = -E * inverse(3^Q) mod 2^L.

For example the first-crossing words 1101100 and 1110100 have slope 81/128. Their respective least sources are 59 and 7, numerators 85 and 73, and endpoints 38 and 5. The larger numerator gives the smaller relative endpoint. An upper bound remains valid, but maximizing E is not a substitute for optimizing the source-dependent obstruction.

## Delete the parity-tree enumeration

Failure of descent at a FIRST crossing with Q odd steps requires

    2 <= b <= floor(H_Q/(2^L-3^Q)).

For Q<=Q_cap let M be the maximum of these exact floors. Every source above M is handled symbolically; only 2,...,M needs replay. The zero-odd case is immediate even-source descent. A qualifying first crossing must occur by bit_length(3^Q_cap). A source outside that event window is not called convergent or divergent.

Fresh checks:

* Exhaustive depth-32 audit: 9,003,202 first-crossing cylinders, each independently scalar-replayed; zero counterexamples. There are still 41,347,483 unresolved prefixes at depth 32.
* Same conditional claim by the envelope: Q_cap=20, M=108, only 107 source checks. 100 cross and descend inside the window, seven are outside. Approximately 84,142-fold fewer candidates, not a claimed runtime ratio.
* Q_cap=10,000: M=5,624,777, maximizing envelope Q=9,616, event horizon 15,850. All 5,624,776 exception sources cross and descend. Independent Python and C++ implementations agree on 19,623,309 scalar steps, maximum observed first crossing 224 at source 1,126,015, and maximum observed odd count 141.

This certifies the bounded conditional statement for arbitrarily large positive sources as well as the checked small sources: when their first crossing has at most 10,000 odd steps, that crossing gives descent. It DOES NOT prove every source reaches a first crossing, or establish the unrestricted coefficient-stopping-time conjecture.

## Artifact regression and implementation checks

The supplied B12/B16/B20/B24 artifact was freshly replayed: 190,245 rows and 3,347,383 future steps, all closed, zero slope-wait cases. B24 remains 172,868/172,868 with maximum extra length 263 at source 13,421,671, ending at 12,335,167. B24 reverse membership was not independently rebuilt in this pass; a separate Python rebuild matched all 144 B12 rows.

The global envelope evaluated at the observed first crossings leaves 27 and 47 inconclusive. Their actual crossings are T^59(27)=23 and T^54(47)=46. Conditioning on the known B24 prefix removes 27. Source 47 needs prefix length 39 for the conditioned comparison; 27 needs only 17. These bounds do not independently predict crossing times.

The full downloadable audit has 12 passing unit tests, including bounded exhaustive envelope sharpness, the monotone pre-crossing credit, invalid-cylinder transfer, budget exhaustion, and forged-prefix rejection. Only the portable exception-window checker and its result are retained here; no CI run is claimed.

## Run

    python experiments/collatz_deletion_audit/first_crossing_window.py --odd-cap 10000

Expected result: `CONDITIONAL_FIRST_CROSSING_VERIFIED`, with `global_collatz_proof=false` and `first_crossing_existence_proved=false`.

## Prior art and remaining obligation

The affine decomposition, parity-vector ordering, and distinction between stopping time and coefficient stopping time are established tools. See Rozier and Terracol, *Paradoxical behavior in Collatz sequences*, arXiv:2502.00948v3, sections 1–2: https://arxiv.org/html/2502.00948v3 . No novelty claim is made for the bounded verification.

The remaining global issue is not removed by renaming variables: one must handle a trajectory that never coefficient-contracts, and unbounded first-crossing cases, or supply a different verified descent/coalescence argument. The code makes neither assumption. Finite positive realizations of increasingly long parity prefixes are not one positive realization of an infinite prefix chain.
