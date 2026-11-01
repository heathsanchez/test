# Cyclone DDS CDR sequence allocation: bounded native verification (2026-11-02 NZDT)

## Verdict
- **WARRANTED_BOUNDED:** A valid-header malformed WStrings message with only 160–164 input bytes and a claimed one-million-element sequence raises peak memory consumption by roughly 56 MiB on native ROS Jazzy, even after PR #625's short-header fix. A three-location sequence-length preflight in `TypeSupport_impl.hpp` prevents this amplification within the tested boundary.
- **CANDIDATE UPSTREAM:** Minimal production fix at [Metalogic Labs](https://github.com/metalogiclabs/rmw_cyclonedds/tree/fix/jazzy-cdr-sequence-length-preflight), commit `aa3aba9982264b1c56e484e48e1d3e5f51c88393`.
- **UNKNOWN:** full worst-case allocation, arbitrary message schemas, C++ introspection behavior, exploitability, release backports, and any further malformed-buffer vulnerabilities.
- The existing upstream [PR #625](https://github.com/ros2/rmw_cyclonedds/pull/625) fixes a *different* short-header problem. This experiment retained it in both comparison arms to isolate a new residual.

## Native evidence
- Successful CI: https://github.com/heathsanchez/test/actions/runs/41344170691
- Runner commit: `2d33af1cd071dec3cb6a3368ec349c3310b626a7`.
- Artifact: https://github.com/heathsanchez/test/actions/runs/41344170691/artifacts/13097918958
- ZIP SHA-256: `9d54d082bf781d2aa03f6c2cf59c5a50a92cf15748339ddd9571154b9ced63ba`.
- Fork Jazzy source commit: `20b192ae744f2fe56767e68081a46ad0d7f7a0ec`.
- PR #625 source commit: `73c2fb62b2be3b752b098f44cc6c41b9c4bbe85a`.
- New patch source commit: `aa3aba9982264b1c56e484e48e1d3e5f51c88393`.
- Three separate compiled libraries: Jazzy baseline, Jazzy+PR625, Jazzy+PR625+preflight. Shared-library SHA256 and actual loaded paths are recorded in artifact.
- Memory budgets: 256/512 MiB `RLIMIT_AS`, CPU/walltime limits, and Docker 1200 MiB cap; every malformed-input trial executes in a fresh process.

## Decisive memory comparison (512 MiB memory budget)

| Native malformed input | PR #625 alone peak RSS | PR #625 plus preflight peak RSS | Improvement |
| --- | ---: | ---: | ---: |
| WStrings bounded sequence, count 1,048,576, 160-byte input | 108,772 KiB | 51,512 KiB | 57,260 KiB |
| WStrings unbounded sequence, count 1,048,576, 164-byte input | 108,788 KiB | 51,340 KiB | 57,448 KiB |

Both outcomes remain a defined `RMWError`; the difference is that the new guard avoids allocating a large destination before validating that at least the per-element CDR length fields exist.

- The bounded allocation census ran 78 cases in each of 3 arms: eight default-message controls and 70 malformed length cases per arm. All eight controls passed; all 70 malformed cases produced defined errors in all arms.
- Four additional *populated* round-trip controls per arm passed: `BoundedSequences`, `UnboundedSequences`, `WStrings`, and `MultiNested`.
- The broader native malformed-input regression ran 224 cases per arm with PR625 and PR625+preflight (two middleware backends × seven layouts × 16 inputs). Cyclone DDS results were exactly unchanged: seven valid acceptances and 105 defined errors in each arm, including all 28 short-header rejections.
- Fast DDS was deliberately left untouched; one or two malformed-case outcomes varied naturally and must not be attributed to the Cyclone source patch.

## Scope of the source fix
The only modified production file is `rmw_cyclonedds_cpp/src/TypeSupport_impl.hpp`:
1. C++ wstring sequences: `deserialize_len(sizeof(uint32_t))` before `resize_field`.
2. C primitive sequences: `deserialize_len(sizeof(T))` before `GenericCSequence<T>::init`.
3. C wide-string sequences: `deserialize_len(sizeof(uint32_t))` before `rosidl_runtime_c__U16String__Sequence__init`.

The source file is byte-identical on upstream Humble, Jazzy and Kilted as checked separately. This does not mean the patch has been natively tested on all distributions.

## Lineage and negative controls
- Initial short-header bug: https://github.com/ros2/rmw_cyclonedds/issues/619
- Existing short-header repair: https://github.com/ros2/rmw_cyclonedds/pull/625
- Prior independent PR625 native test: https://github.com/heathsanchez/test/actions/runs/41340276301
- Initial memory census (two arms, found amplification without patching): https://github.com/heathsanchez/test/actions/runs/41343453629
- Three-arm reduction test: https://github.com/heathsanchez/test/actions/runs/41343843901
- Expanded populated-controls and full malformed-input regression: https://github.com/heathsanchez/test/actions/runs/41344170691
- Next useful action: Propose upstream pre-allocation validation as a separate scoped contribution, include CI artifact and request maintainer guidance on target branch/backports. Do not claim memory OOM was reproduced: the bounds protected the runner, and the observed outcome was a defined error after memory growth.
