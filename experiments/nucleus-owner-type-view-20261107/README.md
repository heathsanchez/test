# Owner-funded capture checking for source/semantic Pi conversion

A mandatory capture check in `value_as_type` still used a fixed 1,024-step
sub-allowance. The patch uses its caller's remaining work and retains the
existing subtraction and capture guard. This is a component experiment.

Reproduce against the qualified minimal-allocation parent, using downloaded
GitHub Actions ZIP artifacts from `heathsanchez/test`:

- parent source: artifact `13509333044`, run `42232448219`;
- current 207 inputs: artifact `13276400289`;
- protected Mathlib prefix source: artifact `13509919383`.

```sh
python replay.py --parent-artifact parent.zip --corpus-artifact arena207.zip --mathlib-artifact mathlib.zip --work replay-output
```

Requires Python 3.12+, Rust/Cargo 1.99.1, patch, and available Cargo dependencies.
The work directory must be new. Exact ZIP/source/input hashes are checked.
Parent RED, candidate full native suite, exact corpus parity, ordinary 4,662-
declaration Mathlib prefix ACCEPT, and a capture-guard-removal countercontrol
must all pass before a bounded receipt is written. Each build uses a separate
output directory. Logs and the receipt are preserved in the work directory.

The new positive is a constructed representation-transfer regression. Corpus
parity does not close the six positive UNKNOWNs. This does not establish full
Mathlib acceptance, independent unseen-task discovery, performance superiority,
or exponential improvement. No selected-default or release change is included.
