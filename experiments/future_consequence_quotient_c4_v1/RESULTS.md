# Future Consequence Quotient C4 V1 Results

## Terminal verdict

**PASS — BOUNDED CAUSAL REPAIR QUALIFICATION**

Replacing immediate prefix credit with continuation-major candidate comparison reduced the unchanged C4 cost from 266 to 161 charged verifier calls, saving 105 calls or 39.47 percent. Every continuation probe was counted. All controls remained correct.

This is not a prospective result: C4 had already been exposed by V1, and the repair was designed from that failure. It establishes a bounded post-failure causal repair and motivates a fresh held-out test.

## Exact measurements

| Condition | Verifier calls | Correct |
|---|---:|---:|
| Cold immediate | 266 | Yes |
| Future consequence | 161 | Yes |
| Exact separator ablation | 181 | Yes |
| Continuation-order operator ablation | 266 | Yes |
| Matched sham | 266 | Yes |
| Answer memory | 266 | Yes |

The four leading candidates had the same immediate verifier profile:

`[0, 0, 0, 0]`

The later continuation

`transpose → rotate_rows → invert`

produced the profile

`[0, 0, 0, 4]`

and separated the ultimately accepted leading candidate `flip_h`. Removing that exact continuation increased cost from 161 to 181 calls. Removing continuation-major ordering entirely restored the 266-call cold cost. Sham state and answer provenance also remained at 266.

Exact-separator ablation removed 20 calls, or 19.05 percent of the 105-call advantage; it did not eliminate the entire gain because other continuations also reach accepted equivalent programs. Necessity is therefore established for part of the measured advantage, while the full advantage is causal to the continuation-major operator family.

## Formal result

The accompanying Lean file verifies, without `sorry`, that full future equivalence is an equivalence relation, respects every action in the supplied action system, supports descended actions and outcomes on the quotient, contains every adequate action congruence inside it, and forces every adequate abstraction to distinguish a continuation-separated pair.

## Classification boundary

The experiment establishes that an existing continuation inside the supplied action language can distinguish an immediate-credit collision and improve charged search cost on the frozen repair target. It does not establish:

- a fresh prospective cross-domain transfer;
- complete construction of the behavioural quotient;
- convergence of bounded continuation profiles;
- a newly generated operation outside the existing monoid;
- generator genesis or expressive language development.

The most consequential residual is now external validity: freeze the same mechanism and test it on a genuinely unseen target. Separately, generator genesis requires certified non-membership of a newly proposed operation in the old generated monoid.
