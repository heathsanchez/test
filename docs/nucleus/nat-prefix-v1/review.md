# Review of the Nat prefix candidate

Reviewed local working tree against exact semantic equivalent of 84c35be. Runtime source is published as e5916cf9d2863377d84a717604ef1da452eb62ea (parent implementation 3915c4f827430e061831507883a37e947c8a8031).

No critical or important issues remain in the reviewed change. The reviewer independently ran all 16 new tests and confirmed 157 total passes in the complete test log. No complete-checker runtime dependency was introduced.

The reviewer found that the first Char field-order mutation changed a shared expression used earlier by Nat.le, so it failed before the intended boundary. The fixed test uses the isolated DataProof fixture, swaps both field arguments, and reaches DataProof admission with UNKNOWN. The trace is preserved in lineage/char-rule-review-fix.log.

Minor follow-up: the Nat.le.below metadata-control test name mentions authority, but it exercises metadata equality rather than the separate prior-certification guard. That guard was inspected and found structurally correct. A direct absence-of-certification test remains desirable; no such test is claimed here.

The reviewer did not judge full corpus closure, hosted CI, closure of all UNKNOWNs, or unrelated preexisting kernel behavior. Those remain separate evidence boundaries.
