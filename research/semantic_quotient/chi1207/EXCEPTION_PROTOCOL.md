# Adversarial out-of-family exception probe

This protocol is additional to the already qualified duplicate-param state quotient.
Exact base/head pins unchanged from FROZEN_PROTOCOL.md.

Question: Does prevalidation in proposed chi PR 1207 make ALL failed route registrations
leave the router structurally unchanged, or only the duplicate-param-key family?

The original PR claims only the duplicate-key family. A new other-failure probe
must not turn a narrower upstream claim into a purported bug in the PR.

Freeze independent grammar before implementation:
- initialize one valid existing route under prefix /a/;
- generate candidate malformed regexp patterns using syntax tokens [, (, * and \\;
- construct a new route /a/{x:EXPR} or /z/{x:EXPR}, no duplicate parameter names;
- require a native regexp parser error, capture the actual panic text and assert it
  is an invalid regexp, not a malformed route delimiter or duplicate-name panic;
- compare bounded serialized router-trie state before and after the recovered panic;
- confirm original preexisting route still dispatches, with a bounded 150 ms deadline;
- repeat under exact source base, contributor head and one-site early-call ablation.

Report ALL observations, including null/no mutation. A changed trie alone is NOT
necessarily observable misrouting or an upstream defect; it only rejects the
stronger, unclaimed hypothesis of fully atomic invalid-registration behavior.
Do not send unsolicited GitHub comments or modify upstream repositories.

The grammar was selected after reading source, so this is a targeted scientific
falsifier, not autonomous discovery of failure families.
