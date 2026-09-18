# Collatz macro-bank qualification V1

## Verdict

The bank passes bounded independent replay, canonical serialization, fresh-process
restart, and targeted-removal checks. It fails promotion as a forward-step or
coverage advantage over direct iteration. Collatz and universal RIGID-component
termination remain unproved.

This is a retrospective replication of the cohort from run 35327397877, pinned
to source commit 91742a2d544e9a4e46d2b936560000b8ae6f5643. It is not a new sealed
holdout and not full QCKN V1 reference conformance. The frozen QCK/QCKN branches
are unchanged. The S_k obstruction, 119/104 audit, and fixed-source countdown
files are preserved unchanged.

## Declared contract

- Shortcut T on positive ordinary integers, exact arithmetic only.
- Training sources: selected odd n in [3,8191]; 252 sources, 481 distinct macros.
- Evaluation: the same 162 selected q=0 RIGID sources in [8193,16383], K=96.
- Macro: at most 12 anchored odd/even episodes, with exact affine coefficients.
- Applicability: actual replay must match every episode, including anchor counts.
- A path template alone does not assert descent on every input. Each successful
  application must supply (n,t,y) and independently establish T^t(n)=y<n.
- Remaining failures are bounded search/portfolio residuals, not expressivity
  obstructions or evidence of universal nontermination.

## What changed

`collatz_macro_authority.py` uses only the Python standard library and does not
import the discovery implementation. It reconstructs affine coefficients through
rational function composition, checks template identity, replays parity guards
with ordinary shortcut steps, and independently checks every source-to-descent
certificate. Corrupted coefficients, bad endpoints, stale authority snapshots,
and corrupted bank digests are rejected. Its source hash is part of the contract.

Acquisition validates an actual training descent for every proposed macro,
including checking that a bounded training loop really found descent. Promotions
are recorded separately as content-addressed evidence events referencing the
contract event. The compiled bank contains ordered guarded templates and explicit
revocation identities, not the training histories.

Each evaluation arm runs in a new process. WARM imports no discovery module and
loads only the canonical bank and common evaluation cohort. RAW_HISTORY receives
the selected training source identities and reacquires the bank. It must reproduce
the same bank digest and exactly the same evaluation rows. This demonstrates
avoidance of repeated acquisition; it does not establish superior solving cost.

This small domain-specific event/serialization format is not MG2 and does not
implement the full QCKN conflict, concurrent merge, or transitive-dependency
protocol. No full runtime-conformance claim is made.

## Controls and measured results

| Arm | Closed / 162 | Counted forward steps | Training sources reprocessed |
|---|---:|---:|---:|
| WARM, restarted bank | 88 | 188674 | 0 |
| RAW_HISTORY, reacquired bank | 88 | 188674, excluding acquisition | 252 |
| SHAM, same bank restricted to m >= 10^100 | 0 | 4182 | 0 |
| Targeted ablation of successful template identities | 61 | 195102 | 0 |
| COLD, ordinary direct iteration | 162 | 5459 | 0 |

WARM's count is 4182 common endpoint-preparation steps plus 184492 template-replay
steps, including failed attempts. Ablation similarly uses 4182 + 190920 steps.
For each source, COLD receives at most that source's WARM preparation-plus-replay
step count and stops at its first descent. Every WARM-closed source is explicitly
required to close in COLD too. COLD uses no macro bank.

The metric counts ordinary forward steps, not total wall time or all arithmetic.
It excludes the shared cohort classifier's overhead and final independent
certificate-verification overhead. The cohort already provides genuine future
endpoints; their traversal cost is charged explicitly. These results must not be
presented as an end-to-end runtime benchmark.

The SHAM changes the applicability domain deliberately; it is an irrelevant-bank
control, not an equally applicable competitor. The targeted ablation removes the
union of template identities used by successful WARM certificates, chosen after
the replication run. Alternatives still close 61 cases. This is a diagnostic
causal coverage check inside the macro runner, not a prospective policy test.

## Interpretation and next mathematical target

The retained templates contribute 27 closures relative to this targeted ablation,
and the canonical bank avoids rerunning training. However, direct iteration
closes all 162 selected sources with far fewer counted steps. In particular,
the 74 unclosed macro cases are not hard cases for the matched forward baseline.

There is also a structural domination proof for this particular implementation.
Every successful WARM certificate is at time t=k+arg, where k is at most the
charged preparation depth and arg is at most the charged template replay steps.
Consequently t is within that source's COLD allowance. Direct iteration checks
every preceding state and necessarily sees the same descent or an earlier one.
On unresolved sources COLD never exceeds its allowance either. Thus COLD's
coverage is at least WARM's and its counted steps are at most WARM's. This exact
step-by-step macro implementation cannot validly pass the forward-step advantage
gate; changing the representation/execution would require a new cost contract.

The proposed speed/reach compounding claim is therefore rejected. Reusing a
verified artifact and outperforming a strong baseline are different claims.

The mathematical objective remains termination within recurrent RIGID components.
A useful next candidate must supply a universally justified consequence or an
actual reduction in the strongest baseline's work. Trying many fixed forward
words with exact step-by-step replay is not demonstrated to supply either.
Candidate directions include symbolically certified applicability/descent guards
that avoid replay, or a well-founded rank covering every internal transition of
a universally sound component. Neither is established by this qualification.

## Reproduction and CI meaning

```
python -m unittest discover -s experiments -p test_collatz_macro_qualification.py -v
python experiments/collatz_macro_qualification.py qualify --output /tmp/macro-qualification
python experiments/collatz_macro_qualification.py promotion --output /tmp/macro-qualification
```

`qualify` must pass the fixed replication, independent replay, restart, sham, and
ablation checks. `promotion` must fail unless WARM improves coverage over the
matched direct baseline, or matches its coverage using fewer counted steps.
Thus the workflow intentionally ends RED on the scientific promotion gate for
the measured result. It uploads the complete bank, causal evidence, cohort,
revoked bank, per-source certificates, controls and summary before that gate.
This refusal is preserved rather than changing the gate to make the run green.
