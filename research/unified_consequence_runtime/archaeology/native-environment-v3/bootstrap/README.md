The bootstrap prepares the legacy catalog runtime and registers the exact modern
base interpreter before any target source is fetched. Run it with the CPython 3.12.14 controller containing
`packaging==26.3`. `metadata_receipt.py` independently checks the frozen package
metadata and active dependency closure without importing project or runtime code.

```sh
PYTHONDONTWRITEBYTECODE=1 python -B research/unified_consequence_runtime/archaeology/native-environment-v3/bootstrap/prepare_runtimes.py \
  --dest-root qualification/runtime-bootstrap --out qualification/RUNTIMES.json
```

The destination must be new and isolated. Downloads preserve the inherited proxy
and configured CA trust with TLS verification enabled. The official installer and
every legacy catalog wheel must match their frozen SHA256 and byte length. Wheels are
installed offline into fresh virtual environments with dependency resolution
disabled; the resulting package sets must exactly match the catalog. The legacy
22-package pins are retained in `legacy-pins.txt`. Both catalog profiles receive
static metadata validation. The modern profile maps to the controller's base
CPython 3.12.14 interpreter; its 39-package environment is materialized by the
source-preserving admission operation. The bootstrap writes preparation and metadata receipts and runs
no source-native test, candidate search, or historical experiment. Runtime identity
is frozen separately by the admission qualifier after bootstrap completes.
