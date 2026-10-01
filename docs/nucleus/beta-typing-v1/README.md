# Literal-lambda typing substitution

Candidate846bd7aada07ff8187ecb9f3f712efad38f6b205; record basef08aea2a.
Qualification run36832681132 FAILED; candidate846bd7 is REJECTED FOR PROMOTION.
Artifact11148467415, SHA256aa57d3e1b4d3e6c1d8b5ff8fa8d59ae80b3456eb83d0ed9cc7e7828ac7e93958.
Both corpora regress beta-ladder ACCEPT->UNKNOWN. Frozen accRecReduction gains,
but that does not compensate for regression. No wrong verdicts or process errors.

Observed failure: TypeValue::Pi inferred from a lambda has a body opened under
its fresh local. PiBody::Fixed returns that open body at application rather
than instantiating the dependency with the actual argument.

Bounded remedy: for a syntactically literal lambda application, first retain
whole-function inference and domain checking of the argument. Then infer the
body under its lexical context and an environment binding the actual argument.
Use the existing shared inference budget and fresh frame/cache identity.

RED: exact compiled record base reports UNKNOWN on the valid dependent identity
application and all five Nat.decEq.match_1 dependency slices. GREEN: exact hosted
candidate passes all six, including pair n7/n21, deep n21/n36 and fueled-chain.
Full-file results and complete corpus reclosure are still pending.

Fresh review: no bypass of existing typing premises found. Scope limitations:
this is literal-lambda syntax only; returned dependent functions can retain a
consumed-binder depth in the old TypeValue::Pi representation. Do not claim a
general dependent-function representation repair. No demonstrated false
acceptance was established. Full replay and independent checks remain required.

## Corrective iteration

Candidate61d06c7 adds a support check on the inferred type through actual closures.
Only proved absence of the bound free skips re-inference; unknown is conservative.
The exact binary preserves beta-ladder and all6 positive fixtures locally.
Full qualification runs36834015096 against last-greenf08, together with singleton
proof-record reuse. Fresh static review found no new support-visitor blocker.
Do not promote until the full last-green-base gate passes.
