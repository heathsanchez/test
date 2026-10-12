# Capstone V3: cost-obstruction-driven stopping predicate

Run `python cost_genesis.py` in this directory. It imports the adjacent V2 `genesis.py` and `falsifier.py`.

The search tests six *supplied primitive predicates* against 5,896 exhaustive two- and three-state Moore machines and two fixed delayed-distinction adversaries. It uses an independent future-word oracle to reject any predicate that changes the final observable partition, then minimizes the sum of refinement rounds. Only after freezing the selected predicate does it evaluate the untouched named holdouts `contains101`, `mod5`, and `mod7`.

The exact result is in `results.json`. Selection chooses `equal` (with `same_count` tied on this monotone-refinement implementation). Training rounds drop from 17,633 to 8,927, 49.37%. Holdout rounds change from 4/5/7 to 3/2/3. Prior training-family consequences remain protected. This is a bounded synthesis from a designer-supplied predicate grammar; not invention of a new programming primitive, Lean formalization, independent source-family transfer, or superiority over an equally informed executable-ledger baseline.

Independent CI must execute the source and verify the frozen JSON output, including a deliberate negative-control failure.
