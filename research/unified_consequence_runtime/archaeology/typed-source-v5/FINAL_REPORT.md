# V5 typed source inventory — executed qualification and real-source diagnostic

**Verdict: WARRANTED_BOUNDED_TYPED_INVENTORY_ONLY. G2/G3/G4/G5/G6 remain UNKNOWN.** Source inventory is not native verification or a developmental acquisition. The original V4.1 scientific 0/7 RED remains unchanged.

## Source and original authority

Isolated [branch](https://github.com/heathsanchez/test/tree/research/udm-typed-source-inventory-v5-20261017) based on qualified V4.1 ROS-sync source `dc59c8fcee6efede520c531eba5e42e7b84a1a9f`. All baseline files are preserved. Frozen adversarial contract first committed `caa5c620d1386842804490ac71e06afc73792dc8`, then versioned typed inventory code `d3254fa9b56085c6916e08bef7b828226c5019d0`. Original `decisive_native_verify._snapshot`, environment binders, gate, inventory and ledger not modified.

Read-only source `typed_source_inventory_v5.snapshot(root, exact_commit)` authenticates Git commit/tree, regular blob bytes (100644/100755), symbolic-link target blob bytes (120000), and opaque gitlink commit OIDs (160000); all modes remain in a deterministic content-addressed manifest. Internal lexical symlink resolution is supported as **inventory evidence only**; absolute escapes, relative escapes, cycles, directory links, dangling links, and gitlink targets have named UNKNOWNs. No native execution permission follows from a source entry. No sandbox/nonbypassability claim.

## Actually executed CI

- First [qualification run #38966891769](https://github.com/heathsanchez/test/actions/runs/38966891769) on source `c5f0028f1fec879ad731ae963fef9b8cdba6bedc`: **70/70 native Python-unit contracts green** (including nine new actual Git trees/negative controls and inherited source/authority tests). [Artifact 12076035041](https://github.com/heathsanchez/test/actions/runs/38966891769/artifacts/12076035041) SHA256 `9b17b561b6d27493ebea123d081ac7777d4322c9efea3f5a4d0bdef16f8faf13`.
- Additional read-only actual-source [run #38967093241](https://github.com/heathsanchez/test/actions/runs/38967093241) source `ec4824ea63a1f8fa6aab0dd2f4856f4d6ab76e66`: **70/70 contracts green**, explicit typed inventory of pinned `jquast/wcwidth@784d08c6cf6b67e19f34ae5ddb9bb8b4aa4f17fe`. Git tree `016bdbe4de8e62621426020b679054f3a092882f`: **108 regular blobs, one symlink README.rst, one opaque gitlink** (110 typed entries); deterministic manifest SHA256 `70d9b00b968dde7cd0594dcf74943825e702c3a9d49a22edce0b42de5e7eba51`. The original native verifier still correctly refuses nonregular entries. [Artifact 12076050248](https://github.com/heathsanchez/test/actions/runs/38967093241/artifacts/12076050248) SHA256 `b09e02939e13fc23aa4fed77f32105242561d86dad8390b49e6d891ceaff1a13`.
- Neither CI run executed prospective protected native tests, candidate learning, comparators or a coding agent. Only synthetic Git object/unit contracts and a **previously exposed** real wcwidth source inventory were executed. No baseline tie or economic advantage inferred.

## Remaining exact boundary

**Versioned native transport/execution authority for typed Git trees has not been independently qualified.** The preexisting `decisive_native_verify._snapshot` insists on regular files; this is preserved until a separate trusted typed native verifier/transport can prove every original source mode, legal in-tree symlink, source and import identity, protected assertion/collection, and the correct disposition of unresolved links and opaque gitlinks, with negative controls and cold replay. A symlink in README need not be an executable error; an unresolved or imported link can be. Never silently flatten/drop source entries, follow an external path, or relabel V4.1's scientific RED as a new success. Separately retain 2 conditional-tox and 1 dynamic-metadata refusals.

The next prospective G2 trial must use independently frozen *new* tasks after fully qualified typed native authority. The wcwidth result is diagnostic and cannot become a fresh developmental trial. Original G0/G1 warrants preserved; G2–G6 UNKNOWN, as before.
