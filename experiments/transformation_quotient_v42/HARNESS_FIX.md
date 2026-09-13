# V42 Harness Correction

Scientific freeze: `2028f974258daae395d095ac6a57e57185360ce3`

The first strict run passed Q1-Q15 and failed Q16 only.

Cause: the post-freeze hygiene scanner forbade the bare token `product`. The frozen executable kernel imports Python's standard `itertools.product` solely to enumerate the complete finite Cartesian set of observed `(state, action)` authority pairs. It does not contain a Cartesian-product representation candidate, product-factor search, hidden coordinate map, or product decomposition rule.

Correction: remove only the ambiguous bare token `product` from the post-freeze hygiene scanner. Continue forbidding the semantic tokens `cartesian`, `factor`, `coordinate`, hidden challenge-family names, and old topology vocabulary.

No frozen scientific file was altered.
