# Fresh prospective CI execution over independently sealed admission

Feasible without a controller change. This is a static feasibility review; no fresh metadata, task source or outcomes were opened, and no CI job was dispatched here.

The committed screening authority binds `/workspace/udm-v54` and one absolute screening output root. Final public manifest descriptors bind the committed ticket and copied public meter at canonical absolute repository paths. `require_screening_manifest` validates the public envelopes, genuine bound audit, entire ordered meter, exact case descriptors and unchanged controller bytes since screening. It does **not** open the raw `sealed_report.path` target packets. Therefore the CI runner need not receive any sealed raw future screening source or native observations. It can use the exact independently audited public admission manifest and rematerialize its own actual native tasks only after its own fresh freeze and lawful learner release.

The smallest reliable setup is:

1. Use a **new separate** prospective workflow. Leave `.github/workflows/udm-native-environment-selection-v3.yml` and every `ENVIRONMENT_GATE_FILES` entry unchanged after qualification. Commit the prospective workflow before its own scientific freeze.
2. Checkout the exact run commit with full Git history (`fetch-depth: 0`). Recreate a real `/workspace/udm-v54` checkout at that exact commit. A symlink to `$GITHUB_WORKSPACE` fails the canonical-path checks. Do not create runtime/build/evidence files in this checkout: clean Git state is required for freeze.
3. Check that the committed ticket/public meter exist at their **unchanged canonical paths** and exact hashes. Do not rewrite paths, ticket hashes, source commits, audit flags or screening records for CI. The raw screening output root need not be populated; it is an evidence pointer retained in the meter and envelopes, not a fresh CI source authority.
4. Prepare fresh external runner-local runtimes using the independently qualified bootstrap. Run controller fixtures before fresh runtime preparation/freeze so fixtures cannot mutate an already-frozen runtime. Build the current controller venv outside the checkout. Use a fresh runtime path map; the environment gate's old runner paths are not reusable identities.
5. Recreate `/workspace/components` and `/workspace/repos` from the **same exact original pinned source commits** already declared by the environment workflow. They stay outside the canonical checkout. `/workspace/repos/test` may refer to the canonical checkout for original immutable method `git show` operations; its use as an input source repository is distinct from the external authority's canonical descriptor checks. Fetch all pinned original historical method objects into the canonical repository before native execution, without running historical experiments.
6. Call the actual frontier `--write-freeze --repo /workspace/udm-v54 --runtimes FRESH_MAP --out /workspace/qualification/FRESH_CI_FREEZE.json` with a clean commit. Its runtime inventory is fresh and host specific. Then execute the actual qualifier CLI with that fresh freeze and the external components/source-repos paths.
7. Retain all result/cost/native evidence on success **and** failure. A legitimate original MSI tie or native scientific negative is not repaired by modifying the protocol. A workflow green check must describe successful execution/evidence collection, separately from G2/G3/G4 verdicts. Do not label a setup-only/refusal-only job as native qualification.

A canonical checkout can be created without changing tracked source, for example after `actions/checkout` has fetched full history:

```bash
sudo install -d -o "$(id -u)" -g "$(id -g)" /workspace
git clone --no-local --no-checkout "$GITHUB_WORKSPACE" /workspace/udm-v54
git -C /workspace/udm-v54 checkout --detach "$GITHUB_SHA"
git -C /workspace/udm-v54 remote set-url origin "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY.git"
```

Perform runtime/controller setup outside that tree, then from the canonical checkout:

```bash
"$CONTROLLER_PYTHON" -B -m research.unified_consequence_runtime.qualify_native_frontier_v3 \
  --write-freeze --repo /workspace/udm-v54 \
  --runtimes /workspace/qualification/FRESH_CI_RUNTIME_PATHS.json \
  --out /workspace/qualification/FRESH_CI_FREEZE.json

"$CONTROLLER_PYTHON" -B -m research.unified_consequence_runtime.qualify_native_frontier_v3 \
  --repo /workspace/udm-v54 --freeze /workspace/qualification/FRESH_CI_FREEZE.json \
  --components /workspace/components --source-repos /workspace/repos \
  --out /workspace/qualification/FRESH_CI_NATIVE_RUN
```

Use the actual qualified bootstrap flags (`--dest-root ... --out ...`) and original component pins from the unchanged environment workflow. Root must bind their exact implementation in the committed prospective workflow, rather than the placeholders above. Job time must cover bootstrap plus the declared acquisition arms; the environment gate's45-minute job limit does not itself establish sufficient time for multiple3600-second acquisition arms. Wall/native budgets remain enforced by the controller regardless of CI timeout.

The CI check should inspect a real `UDM_NATIVE_FRONTIER_RESULT_V3`, exact execution commit/freeze, preserved original state, genuine native training baseline packet and actual nonzero native costs. A training selection stop should retain its actual cold/profile and informed-ledger runs. Preserve all UNKNOWN obstructions and source-release logs. Only the explicit warranted G2 result can establish bounded G2; a workflow status alone cannot. G3/G4 remain UNKNOWN.

Two practical boundaries need explicit handling:

* **Prospectiveness:** the first learner execution may occur on CI while independently screened raw future data stays sealed locally. A CI rerun after a local learner already exposed the same task is a reproduction and cannot reestablish untouchedness. Freeze/source commit identity never erases prior exposure.
* **Actual coding agent:** a CI-published agent arm binds that runner's actual source/environment paths and starts its meter at handoff. A downloaded artifact after the job ends is not a live executable arm or an actual matched agent. An actual coding agent needs a lawful live execution bridge to that same run during its remaining3600-second budget, or a separate explicitly scoped actual local comparison retained as such. No additional bridge is implemented in the current controller. A CI-native G2 run can retain `PENDING_ACTUAL_EXECUTION` and G4 UNKNOWN honestly.

These are orchestration constraints, not grounds to relax native evidence, change original algorithms, repath signed records, or reset costs.
