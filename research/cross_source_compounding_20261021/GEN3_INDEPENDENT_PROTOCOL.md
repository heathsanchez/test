# Independent Gen3 reproduction and causal search comparison — frozen protocol

Pinned third-party source: go-ini/ini@e2db55b0e088fa4ee0c128aa4ade263cdc1d7f08.
Previously observed native search: "plain\\" -> "plain" at 12 evaluated candidates, run 39540011181.

Independent reproduction must:
- construct the literal trailing-backslash input without calling the Gen3 generator;
- print hex and Go quoted form of each of two serialized representations and both decoded values;
- compare an ordinary string negative control "plain";
- report actual native property PASS/FAIL (a diagnostic observation must not become a green correctness claim).

Comparison:
- warm candidate search uses Gen1 nine seeds followed by supplied bounded mutation grammar;
- cold ablation removes retained seeds, but receives exactly the same primitive grammar and source information;
- strongest equal-information baseline is explicitly supplied the warm seed list and algorithm, hence may make identical decisions; it MUST NOT be handicapped;
- compare wall time and Go/native oracle calls, plus fixture construction and dependency setup.
- restore/restart must reproduce same witness and declared scope.

A source-native witness alone does not qualify economic compounding; human method construction remains unmeasured. Preserve ties, zero-witness, and fail-closed behavior.
