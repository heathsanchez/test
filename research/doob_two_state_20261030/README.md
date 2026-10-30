# Two-state Markov counterexample to an overbroad eliminator identity

**CANDIDATE pending CI**, 30 October 2026. Target text: *Recursive Distillation and Eliminative Discovery*, Heath Sanchez, 9 March 2026, §§8–9, especially Definition 8.1, Theorem 8.1 (E1–E5), §§8.3–9.2, plus the three-line §9.5 summary and stationary-distribution statements. The test does not adjudicate claims about physical reality or universality.

For the irreducible two-state continuous-time Markov generator and killing rate

\[
Q=\begin{bmatrix}-1&1\\1&-1\end{bmatrix},\qquad V=\mathrm{diag}(0,1),
\]

the killed generator \(K=Q-V\) has a strictly positive principal right eigenvector \(h=(1,(\sqrt5-1)/2)\) satisfying \(Kh=-\lambda h\) where \(\lambda=(3-\sqrt5)/2\).

The handbook's bare expression \(Bf=h^{-1}Q(hf)\) violates \(B1=0\): its rows sum to about \((-0.382,+0.618)\). It is therefore *not* a conservative Markov generator under the stated generality. The conservative survival-conditioned generator is instead

\[
\widehat Qf=h^{-1}(Q-V)(hf)+\lambda f.
\]

Here \(\widehat Q\) has off-diagonal rates \(0.618\) and \(1.618\) and row sums zero. The handbook's E1 also requires the *generator itself* to map every nonnegative \(f\) to nonnegative values, which conflicts with E2's baseline recovery: \(f=(1,0)\) is nonnegative but \(Qf=(-1,1)\). Positivity belongs to the **semigroup** rather than to the generator pointwise.

Furthermore, with baseline stationary \(p=(1/2,1/2)\), normalizing \(p\,h\) gives about \((0.618,0.382)\), not the invariant distribution of \(\widehat Q\), about \((0.724,0.276)\); in this symmetric killed example the latter is proportional to \(h^2\). This distinguishes a one-shot exponential/likelihood tilt from a stationary survival-conditioned process.

The honest correction is **scoped**: \(h^{-1}L(h\cdot)\) is a conservative Markov generator if \(h\) is positive and \(Lh=0\), or use the killed principal-eigenfunction/\(\lambda\) shift as above. No general universality follows from this finite counterexample.

## Verifier

- `python3 -m unittest discover -s research/doob_two_state_20261030 -p 'test_*.py' -v`: six exact-form numerical checks (12-digit tolerance), independent of random seeds or simulation.
- `python3 research/doob_two_state_20261030/doob_counterexample.py --assert-original-generator-is-markov`: deliberately exits nonzero on the original proposed identity; CI must reject an unexpected pass.
- Output is an explicit small witness and corrected control; this is **not** a Lean or proof-assistant formalization.
