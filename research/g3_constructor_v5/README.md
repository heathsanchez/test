# G3 V5 — typed, source-bound cache-operation qualification

This isolated research adapter tests a **bounded native state trace** on a pinned
Go package. It is not a self-improving agent and does not prove G2 observation
invention, O1→O2→O3 compounding, owner permission, or economic superiority.

## Scope

- Source identity: exact Git commit, clean original checkout. No target-specific
  repair or source mutation is permitted during a frozen trial.
- Constructor admission: one exported `New`, pointer result or `(*T,error)`,
  simple numeric/string/duration arguments, finite `any`/`comparable` generic
  witnesses, omitted variadic options. Any unsupported form yields `UNKNOWN`.
- Legacy packages without `go.mod`: stage an **untracked, temporary module copy**
  using the explicitly declared repository identity; never write into the
  original source checkout.
- Operation admission: constructed object (or `Build()` result) must expose
  compatible `Set`/`Add`, `Get`, and `Delete`/`Remove` methods.
- Native witness: initial miss, Set/Add, readback, overwrite, second readback,
  Delete/Remove and final miss, with fresh literal key/value witnesses.
- Controls: builder withdrawal, generic-argument compile rejection or explicit
  mutator-disabled observation, then restoration. A mutator-disabled observer
  is **not** proof of independent learned-operator ablation.
- Independent original-package suites and their **nonzero recognized test count**
  are checked by a separate prospective harness, not by this constructor planner.

A qualified receipt means `WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY` at the
named source/test boundary. A green GitHub Actions job can still contain a
scientific `UNKNOWN`. A fresh external owner grant is not implied.

## Reproduce local fixtures

Use Go 1.23+ and Python 3.12+:

```sh
go test ./... -count=1
go vet ./...
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

The stand-alone call is `execute.run_target(Path(source_checkout), source_sha,
Path(output_directory), repo_name="owner/repo")`. `repo_name` is necessary for
legacy modules, and repository SHA/clean-tree checks run before native execution.
The CLI accepts a separately frozen JSON target manifest with schema
`mathgraph.g3.v5.cold.v1`.

Do not run arbitrary fetched source with elevated privileges or secrets. The
prospective GitHub workflows pin external repositories to exact SHAs and use
read-only workflow permissions. Preserve untouched source pools (including V45)
and keep private collaboration records out of public GitHub.
