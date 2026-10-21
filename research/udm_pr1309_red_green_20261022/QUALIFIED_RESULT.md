# Original PR #1309 native RED to GREEN qualification

Qualified run: https://github.com/heathsanchez/test/actions/runs/39649407483 (SUCCESS).
Source: more-itertools/more-itertools, base 1ea82a711c69f590054987b5cb194157f8ce8ac4, head 67fcf640477c78605580f5ee703a54c73c1e7a8a.
Exact author test Git blob: b3a9351595a6fd7f1aa9c1e35978f08106e43df0.
Native pytest node: tests/test_more.py::BucketTests::test_falsey_validator_is_honoured.
Base exit 1: assertion expected [] but got [10]. PR head exit 0: one native test passed.
Cause in source: a falsey callable validator was replaced by permissive default using Boolean or. Explicit None selection in author head resolves targeted test.
Evidence artifact: https://github.com/heathsanchez/test/actions/runs/39649407483/artifacts/12368876300
ZIP digest SHA256 312f840410b700077d54ffcb36748d9bf8e024c8e6addeec62a5d83881abd37b.
Prior negative apparatus runs #39649189546 (wrong node/dirty checkout) and #39649300833 (wrong aggregation directory) retained.
WARRANTED_BOUNDED: exact source-pinned original author test RED -> GREEN on original PR base/head.
UNKNOWN: original full native UDM suite, native G2/G3 acquisition, fair comparative development, full lifecycle economics. No upstream writes, verifier authority or 7-second original horizon modifications.
