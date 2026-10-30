# Lag–Depth Grammar: finite, locally causal NP-verifier falsifier

Source: Heath Sanchez, *Lag–Depth Grammar and Universality Classes of Dynamical Computation* (3 pages), page 3, Lemma 1 and Corollary 1.

## Exact boundary

The paper defines `k(m)` as the number of length-`m+1` substrings of a **single finite trace** of length `N` and claims polynomial-time NP verifiers cannot exhibit exponential grammar support, because the trace eventually has no words after a fixed depth. The latter observation is tautological for **all** length-`N` traces:

    0 <= k(m) <= min(A**(m+1), N-m)  for 0 <= m < N,
    k(m) = 0  for m >= N.

It cannot distinguish local physical computation from a nonlocal oracle.

For any `n >= 2` define the witness `w_n` by concatenating all `2**n` binary words of length `n`. Its length `N_n = n*2**n`. Give an ordinary NP verifier an input `x=0**N_n` and witness `w_n`. The verifier reads the witness **once**, computes parity, and accepts when parity is even, taking `N_n` steps. Instrument the trace as the succession of bits read. Every binary word of any length `d <= n` occurs, so

    k(m) = 2**(m+1)  for 0 <= m < n.

In particular `k(n-1)=2**n` grows exponentially with depth `m=n-1` while the verifier is linear-time in `|x|` and strictly left-to-right. Any fixed uniform depth cutoff is contradicted by choosing `n` larger. A finite trace still trivially vanishes at `m >= N_n`, which is a different (uninformative) claim.

As a recognizably standard verifier, the tests also instantiate SAT with the CNF
`AND_i (v_i OR NOT v_i)` for `N_n` variables. All Boolean assignments are valid
witnesses, and a verifier reading each witness bit and checking the corresponding
tautological clause in two steps per variable generates the same full-support
trace. The family consists of easy SAT instances but is checked by an ordinary
polynomial-time verifier for the NP-complete SAT relation; the claim concerns
**all** NP-verifier traces, not only hard instances. The special witness can be
generated sequentially by an n-bit counter, without nonlocal computation.

## Scope / status

- **WARRANTED within finite explicit construction:** the paper's proposed universal NP-verifier/physical-vs-oracular grammar boundary is false under a uniform-input interpretation. A single finite-trace vanishing statement is true but tautological.
- **NOT CLAIMED:** turbulence experiments or the value of lag-depth words as a heuristic diagnostic are disproved; the test doesn't analyze all possible trace encodings or asymptotic stochastic processes.
- **POSSIBLE REPAIR:** state a fixed trace encoding, observation channel, input-size/depth scaling, causal locality criterion, and null model. Treat grammar support as a finite-sample statistic, not a theorem separating NP verification from nonphysical oracles.

## Verification

Run `python3 research/lag_depth_falsifier_20261030/falsify_lag_depth.py` and `python3 research/lag_depth_falsifier_20261030/falsify_lag_depth.py --json`.

The negative control `--negative-control` **must fail** with `AssertionError`. This checks that the falsifier really rejects the original universal-bound interpretation.
