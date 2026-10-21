# V9b post-first-run prospective-decision audit (no retroactive V9 promotion)

The first V9 sealed evidence at commit 2e3222b1857f8f2df3cc6ca6a45d47d1d5d901e5 executes each owner and headers test before marking skip allowed, so it proves repeated bounded agreement, NOT a cost-saving pre-test eligibility decision.

V9b changes the order of operations only in a separate script: on original V8 historical source/test identity and three accepted exact method-body changes (A, B, C), derive provisional exact-identity-and-edit-shape eligibility before running ANY new header tests. Owner native test remains mandatory and is executed before granting a scoped skip decision. Then independently audit the proposed omitted headers test to falsify proposals. Include malicious D code with owner negative, test-identity mutation, and source-extra mutation as negative controls.

This does NOT prove Python general noninterference or release permission: native traces and tests in the same CI still audit each proposal. The conventional cached-coverage baseline with the SAME V8 history and source diff yields TIE. Record hypothetical avoided native process time only and cost all audit runs explicitly.
