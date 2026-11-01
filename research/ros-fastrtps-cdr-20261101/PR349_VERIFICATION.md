# Fast-CDR PR #349 — independent ROS 2 Jazzy verification (2026-11-01)

## Result and boundary

**WARRANTED (bounded):** Source-only fix from [eProsima/Fast-CDR#349](https://github.com/eProsima/Fast-CDR/pull/349) eliminates the observed Fast DDS crashes in the tested ROS Jazzy CDR matrix, without failing its valid-message positive controls. This is not a claim about every malformed CDR input, every architecture, or the original PR's newer ABI in ROS.

- Exact upstream PR head **built**: `1eaa6c809d464fb5d1c1b9be03ffcc4adc29c2ed` (Fast-CDR 2.4.0), parent `e92fa060825c21572f56a44656c02cbe2b06069c`.
- For compatible native ROS runtime, applied *only the PR's `src/cpp/Cdr.cpp` patch* to Fast-CDR `v2.2.8` at `1bc9c919311ffce555b445560bf7ae062a4e1c72`. The 11-line patch is stored in the artifact, SHA-256 `0776fb2143ac8b2d8363fcc8f8bb03dad58e12e582633319fa1763d4c103c668`. No other source modifications.
- **Two native runs of the same 224-case matrix**, one per arm, 448 total process-isolated cases. Seven `test_msgs` layouts, 16 serialization variants, two RMW backends, real ROS Jazzy packages.
- Exact workflow/experiment commit `23b3274dfdc620bac2e9e565eae871ebf9186dbc`: [run #41280186916](https://github.com/heathsanchez/test/actions/runs/41280186916) — **SUCCESS**; [evidence artifact #13072589862](https://github.com/heathsanchez/test/actions/runs/41280186916/artifacts/13072589862), ZIP SHA-256 `61c70680bb2fc70d7e50cb5b9b01c367187267e5d8be2643b1d048c887e1d7bb`.
- Baseline `libfastcdr.so` SHA-256 `a00aa3d5b5c44be5670902331bf598a3a8cdb5221aa5093fe0ed813e375abb8f`; patched `07704032e2f0e72f214189ecd4230633ec3adacae0dbfae67c00d4054f1ec95f`. Runtime `/proc/self/maps` checks confirm each ROS process mapped the intended distinct `libfastcdr.so.2.2.8`.
- Packages: `ros-jazzy-fastcdr 2.2.8`, `rmw_fastrtps_cpp 8.4.4`, `rmw_cyclonedds_cpp 2.2.4`, `rclpy 7.1.12`; the artifact records exact package build versions and Docker image identity.

## Observations

| Outcome, Fast DDS (112 cases per arm) | Baseline | Patched |
|---|---:|---:|
| Process signals | 24 | **0** |
| Timeouts | 1 | **0** |
| Defined errors | 71 | **101** |
| Accepted | 16 | 11 |

All **seven valid-message controls for Fast DDS** passed in both arms, as did all seven Cyclone DDS valid controls. For `00 00 00 01` (header-only), `Arrays`, `Strings`, `BoundedSequences`, `UnboundedSequences`, and `MultiNested` changed from signal termination to an error. `BasicTypes` changed from an inappropriate acceptance to error; `WStrings` remained an error. Four additional options/padding variants produce the same transformation in the six affected message layouts. Overall **30 Fast DDS outcomes changed**, all to defined errors.

**Cyclone DDS is a separate unresolved problem:** malformed-buffer crashes and timeouts remain (baseline 16 signals + 4 timeouts, patched 15 signals + 4 timeouts). One independent Cyclone outcome fluctuated from signal to error across runs; this is not evidence that Fast-CDR fixes Cyclone.

## Residual and lineage

- **WARRANTED_BOUNDED:** Native failure reproduced on installed Jazzy and fixed by precisely the upstream change ported onto the Jazzy ABI, with valid controls preserved.
- **CANDIDATE for upstream acceptance:** PR #349 remains open at this assessment. The exact 2.4.0 PR head builds, but was not substituted into Jazzy because of ABI/version differences.
- **UNKNOWN:** exhaustive malformed-input rejection, all machine architectures, sanitizer safety beyond tested cases, regression on other Fast-CDR consumers, release/backport timing.
- **Not a duplicate PR:** This is independent evidence supporting the pre-existing PR #349, not a competing fix.
- **Negative controls preserved:** Earlier runs failed on ROS `set -u` setup, and a harness `LD_LIBRARY_PATH` override that hid Cyclone DDS; neither was counted as production failure. The final run restores the full ROS loader path, records library mapping, and asserts the controls.
- **Upstream publication:** An attempted comment on PR #349 was rejected by the connected GitHub integration (HTTP 403), so no claim of posted maintainer feedback is made.
