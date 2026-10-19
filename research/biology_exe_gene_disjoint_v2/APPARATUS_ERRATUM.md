# Apparatus-only correction — original protected ExE source remains unopened

**Frozen method receipt**: commit `15ee43b5092af1290d0bb950e4dcbb25f1254989` (method, protocol, synthetic tests, evaluator and workflow; all before any ExE numeric outcome opened). Initial [GitHub Actions run #39226218895](https://github.com/heathsanchez/test/actions/runs/39226218895) stopped at the synthetic smoke step. No real ExE source acquisition or hidden-target outcome scoring occurred.

**Observed apparatus obstruction**: naming the local script `select.py` shadowed Python's standard-library `select` module imported by `socket`/`selectors` under CI's fresh process, causing a circular Python import. Local success had happened because `select` was imported earlier by the test harness; this is NOT a scientific failure or success.

**Allowed correction only:** rename `research/biology_exe_gene_disjoint_v2/select.py` to `predict.py` (byte-identical except path), and change only the references in test/workflow/protocol/evaluator descriptions. No selector formula, source, parser interpretation, hypotheses, target dataset, thresholds, split, seed, baseline or outcome interpretation changed. Preserve original CI run and commit as negative apparatus lineage.

The first ExE outcome remains sealed; do not interpret the apparatus correction as permission to tune after observing source outcomes.