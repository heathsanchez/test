# G2 native admission repair — source-preserving qualification only

State: CANDIDATE pending CI. Original frozen G2 experiment and scientific RED preserved unchanged.

Historical original run: https://github.com/heathsanchez/test/actions/runs/39062754584
Original upstream source: pallets/itsdangerous@096c8d42545d3b68ea21a4f890fb2b2d8979c0bd (tag 2.2.0)

The prior native admission collected two import errors, no executed assertions. Both were caused by missing freezegun. The exact upstream-authored requirements/tests.txt pins pytest 8.1.1, freezegun 1.4.0 and transitive test dependencies, but the original workflow installed the latest unpinned pytest without those dependencies.

This new branch does NOT change target, upstream source, original tests or developmental search. It verifies the already frozen original SHA, installs the original test-requirements lock, asserts all seven pinned dependency versions, and runs the full native author-test directory with no skips/errors/failures. Source test ASTs must contain real static Python assertions. Wrong SHA and dirty source are independently exercised as fail-closed negatives before any native subprocess. The admission receipt distinguishes partial skip, genuine native failure and apparatus errors, hashes the original Git tracked source tree (not only the pin descriptor), and archives original stdout/stderr/JUnit/pip freeze, refusal controls and source identities.

Passing this remediation qualifies only original native test admission, not a new protected failing obligation and NOT G2. No autonomous O1->O2, second source-distinct task, ledger/agent comparison, economic advantage or external action authority executes. G2-G6 remain UNKNOWN. Itsdangerous is now exposed calibration and cannot become a retrospectively fresh prospective win.

No third-party, default-branch, product, deployment, or ROS mutation is authorized by this branch.
