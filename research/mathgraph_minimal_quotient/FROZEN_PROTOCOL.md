# Frozen protocol — JPL-style observational quotient on previously unseen HTTP parser PRs

Frozen **before inspecting any code patch**. Created on 15 October 2026 NZDT. PR titles/bodies and current base/head SHAs were already inspected for selection; **NOT a blinded bug discovery**.

## Targets (read-only, no upstream writes)

- Primary: python-hyper/h11 PR #206, base `62c5068c971579d61fa1b55373390e12f25fd856`, author head `05972a8b34faeb91c22b9a6283da84e45e7f0781`.
- Transfer A: python-hyper/h11 PR #198, same base, head `46a076d96fbf9b18868c45ddfd2dcc0e2077f2a5`.
- Transfer B: python-hyper/h11 PR #207, same base, head `ec2e2dbbdc61587911dda3dd5f868f14ab0733f4`.
- Reuse the **identical source-independent probe generator, observer and minimizer** without per-PR code, target functions, input literals or expected labels.

## Hypothesis / state abstraction

Given a finite, preregistered public HTTP message grammar and a finite set of chunk schedules, group source/runtime states by their **observable future dispositions**. Source states are equivalent only *relative to that finite observation language*, not universally. Preserve outcome categories (ACCEPT, REJECT, INCOMPLETE, OTHER) and exact event payloads independently; do not erase consequential event/value differences to make a score look good. Candidate wire fields: request line, header names/values, optional whitespace/folded line, header count, resource cap, whole/split/bytewise transport.

From the same wire, compare chunk schedules; every difference must be replayed natively on exact source revisions and reduced by independent minimization to a reproducible, smallest-in-the-generated-set separator. Use prefix/suffix continuation observational equivalence to construct a quotient and exhaustively choose a smallest distinguishing suffix basis where computationally feasible. Negative controls: no change across equivalent chunk schedules on ordinary small requests, stale revision rejection, arbitrary source edit invalidates result, no witness if both revisions behave alike, and separate exact event payload equality vs coarse accept/reject.

## Source bridge and baselines

Automatically inspect Python AST conditional/guard expressions in functions changed by git diff; produce a source-location-pinned projection of tested guard fields. This is a structural candidate, **not a proof that all source behaviours factor through it**. Native calls must import the original checked-out h11 implementation and use its public `Connection.receive_data/next_event` API; never use a hand-written mock parser to call an upstream difference.

Simple baseline: exact diff summary plus GitHub CI; strong information baseline: a conventional reviewer given PR title/body, source, original tests and exact CI could infer the author-described issue. No claimed reviewer superiority without equal-information blind timing. Disclose absence of independent normative oracle, the source-grammar choice and incomplete observational horizon.

## Predeclared acceptance

- Tier 1: exact base/head source checkout, deterministic real native calls, independently observed full events and a minimal (within search grammar) differing input or a warranted null result for each target.
- Tier 2: an explicit finite observational quotient, with a minimum or verified greedily-selected separating suffix basis, strict count of erased distinctions and native negative controls; no false assertions of global minimality.
- Tier 3 (NOT automatically implied): fully source-faithful automated semantic compression of arbitrary code, independently synthesized *new* operation/test grammar, correct novel bug absent PR author disclosures and superiority to informed reviewers. These remain UNKNOWN unless independently established.

No Gmail, Render, upstream comments, third-party GitHub App installations, code writes to original repos, PR merge, production Cloudflare or mathgraph.org changes.
