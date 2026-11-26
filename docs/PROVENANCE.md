# Source provenance

The standalone repository extracts Nucleus's existing implementation from
`heathsanchez/test`. It retains 720 commits of subtree history, including
earlier experiments and negative results.

| Identity | Value |
| --- | --- |
| Original repository | <https://github.com/heathsanchez/test> |
| Original commit | `578697991a903ab78d344aa71165d465bef3c3d7` |
| Original directory | `metatron-kernel/` |
| Complete imported directory tree | `d55d582a0c32276fc981a713867999faf730c6f2` |
| Qualified Rust `src/` tree | `362242c265ee2b1758645c78ad141ad78bf6f8c2` |
| Standalone import commit | `3b6c43d90e46d453d75d7e7b643fa168814372b9` |
| Import tag | `source-import-2026-11-26` |
| Original qualification | [Actions run 45681083460](https://github.com/heathsanchez/test/actions/runs/45681083460) |

The imported commit's complete root tree is identical to the original
`metatron-kernel/` tree. Moving a subtree to the repository root changes
commit identities. The [history map](history-map.tsv) relates every retained
original commit to its extracted counterpart. Authors, dates and commit
messages are retained.

Extraction used the upstream `git-filter-repo` tool with
`--subdirectory-filter metatron-kernel`, in a disposable clone. The original
research repository and Arena source pin were left intact.

## Runtime identity

The checker source, Cargo manifest and lockfile, launcher and frozen flags
are preserved byte for byte. Their SHA-256 hashes and Git blob identities are
recorded in [the import manifest](../evidence/source-import-20261126.json).

```sh
python3 scripts/verify_source_import.py
```

The crate and executable retain the historical `metatron-kernel` name so the
source and launcher can be verified unchanged. The public project name is
Nucleus.

New standalone material consists of the README artwork, license text,
contribution guidance, toolchain pin, CI, import identity check, recorded-corpus
replay tool, qualified test runner, qualification record and source history map. Build paths in the
Arena and formal-model documentation are adjusted for the repository root.

## Historical research tools

Earlier files under `scripts/`, `evidence/` and `formal/` retain their original
scope. Some research tools refer to sibling `experiments/` directories in the
original repository, or to original GitHub Actions artifacts. For example,
`qualify_beta_entry_20261126.py` expects the original research layout.

Resolve such historical dependencies against the
[pinned original tree](https://github.com/heathsanchez/test/tree/578697991a903ab78d344aa71165d465bef3c3d7).
They are not needed for the documented standalone build, runtime or regression
suite. Use `scripts/replay_recorded_beta.py` for the standalone migration
qualification.

The current Arena descriptor remains pinned to the original source until the
new repository has been published and qualified. A source-location update
must retain its configuration and explicit capability limits.
