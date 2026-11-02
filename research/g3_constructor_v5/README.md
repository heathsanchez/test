# V4: typed cache-operation bridge

This experimental adapter tests a **finite native state transition**, rather
than merely checking that a constructor returned nonnil.

## Bounds

- Go modules with a root-level exported `New` and a constructed or
  `Build()`-derived object supporting exported `Set`, `Get`, and
  `Remove`/`Delete`.
- Constructor arguments are inhabited by a fixed small grammar:
  primitive values, `time.Duration=0`, empty variadic tail, and
  `string` for `any`/`comparable` generic parameters.
- Source-native reflection performs initial miss, Set, Get, overwrite,
  Get, remove, and final miss with independently chosen witness values.
- Execution checks the **exact source commit** and clean tree. It performs
  a builder or type-parameter ablation followed by native restoration.
- A pass means `WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY`; it does not
  establish autonomous invention, better-than-baseline performance, or
  strict G3 closure.

Unsupported API shapes, unsafe/ambiguous native execution, absent ablation,
and source drift become an explicit UNKNOWN. The V45 reserve is not used.

## Reproduce local fixture tests

From this directory with Go 1.25+ on `PATH`:

```sh
go test -count=1 ./...
go vet ./...
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

To replay an exact local Git checkout, call
`execute.run_target(Path(repo_root), commit_sha, Path(output_directory))`
from Python with this directory in `PYTHONPATH`.

The CLI `execute.py --targets manifest.json --output output/` can clone
configured repositories, but do not run unfamiliar target code with elevated
credentials or privileges. Prefer a restricted clone step and source-native
execution inside a sandbox.
