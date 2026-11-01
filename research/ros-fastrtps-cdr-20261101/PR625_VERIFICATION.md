# ROS 2 Cyclone DDS PR #625 — independent native verification

Evidence date: 2026-11-02 NZDT. GitHub Actions run: 2026-11-01 UTC.

- Issue: https://github.com/ros2/rmw_cyclonedds/issues/619
- Existing upstream PR: https://github.com/ros2/rmw_cyclonedds/pull/625
- Claim: **WARRANTED_BOUNDED** on native Jazzy for the 0–3 byte malformed-header case. Not a broad proof of deserialization safety.

## Exact source and experiment identity

- PR head: 73c2fb62b2be3b752b098f44cc6c41b9c4bbe85a, Kilted parent: 789417d28d275800ad28fe9bd11dd358406b3cce.
- Baseline and patch applied on the same Jazzy source commit: 20b192ae744f2fe56767e68081a46ad0d7f7a0ec.
- The original serdes.cpp blob on Jazzy is identical to the same file on PR #625's Kilted parent. Only the six-line source fix is applied to the second arm.
- Baseline librmw_cyclonedds_cpp.so SHA-256: a530971e85e534b59bcbee6f295eb90dd004c57f1547e9216b15f5681a68068e
- Patched librmw_cyclonedds_cpp.so SHA-256: e7ca14d5913ea9f37c32c478fff7ba67885055af770f1cad4454264ca12c2434
- Both Python runs independently confirmed their loaded library paths via /proc/self/maps.
- Runner commit: 1d939c2fa99baa6263448b53016348d84479ecc7.
- Successful native run: https://github.com/heathsanchez/test/actions/runs/41340276301
- Evidence artifact: https://github.com/heathsanchez/test/actions/runs/41340276301/artifacts/13097331381
- Evidence ZIP SHA-256: 09983a07b7389d90991ffb6af6217aef15ff41ae8486c456adaadb4f62106457
- Environment: ros:jazzy-ros-base, rmw_cyclonedds_cpp 2.2.4, rmw_fastrtps_cpp 8.4.4, rclpy 7.1.12; exact package builds and container identity preserved in artifact.

## Comparative results

448 process-isolated executions: two arms by two RMW backends by seven message layouts by sixteen inputs.

| Outcome (Cyclone DDS, 112/arm) | Unpatched | Patched |
| --- | ---: | ---: |
| Process signals | 15 | 0 |
| Timeouts (6s) | 4 | 0 |
| Defined deserialization errors | 82 | 105 |
| Accepted | 11 | 7 |

All **28 cases** of 0–3 byte serialized input (seven message layouts times four lengths) return defined errors with the patch. Baseline: 15 signals, four timeouts, four inappropriate BasicTypes acceptances, and five errors. The 14 valid controls across both RMW backends passed in both arms.

One unrelated Fast DDS negative control (BoundedSequences, le_two) varied from timeout to signal between runs; Fast DDS was not modified. It is a variability caveat, not a Cyclone regression. Fast-CDR PR #349 was validated separately in run #41280186916.

## Residual, negative experiments and lineage

- WARRANTED_BOUNDED: Native Jazzy 0–3-byte boundary fixed by exact PR #625 source change with positive controls.
- UNKNOWN: Exhaustive malformed CDR safety, reported high-memory fuzz lead, other architectures, Kilted exact PR binary, production integration, all release backports.
- Avoid duplicate fix: Existing PR #625 by Rahul-cs50 already addresses the root cause.
- Attempt to comment upstream on PR #625 returned 403 Resource not accessible by integration; verification has not been posted to that PR by this work.
- Earlier setup run #41340131240 failed because colcon --log-base was positioned after the build subcommand. It was corrected; no production inference was drawn from that run.
- Smallest next action: Provide the source-pinned evidence to PR #625, then track its merge and Jazzy/Humble backports. A bounded-memory fuzz investigation remains separate and unverified.
