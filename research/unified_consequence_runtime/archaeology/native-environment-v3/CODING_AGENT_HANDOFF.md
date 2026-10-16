# Actual coding-agent handoff observer

Prepared source-free. No prospective metadata, task source, native outcome, ARM,
ledger, or target CAS has been accessed. The helper has only been executed against
its synthetic input-format fixtures. It does not establish scientific success.

## Parent-side publication hook

The trusted parent runs this at publication of all three immutable files:
`AGENT_ARM.json`, `AGENT_PARENT_RECEIPT.json`, `AGENT_AUTHORITY.json`.
The authority is the last file written by the real controller. Record its SHA256
in parent custody; do not let a source-reading evaluator self-authorize by hashing
an editable ticket. The metadata SHA is the previously frozen exact bytes.

```
python -B training_history_projection.py \
  --arm /ABS/ACTUAL_RUN/AGENT_ARM.json \
  --authority /ABS/ACTUAL_RUN/AGENT_AUTHORITY.json \
  --authority-sha256 PARENT_RECORDED_SHA256 \
  --metadata /ABS/REPO/research/unified_consequence_runtime/archaeology/native-environment-v3/FRESH_TASK_METADATA.json \
  --metadata-sha256 FROZEN_METADATA_SHA256 \
  --out /ABS/NEW_TRAINING_ONLY_SHARED_HISTORY.json
```

Invoke immediately rather than waiting for subsequent cold/warm/ledger searches.
The real controller's agent meter starts at arm publication and includes common
acquisition wall time. Projection and handoff delay consume the remaining clock.
The helper records its elapsed time, exact source SHA and all input path/digests.
Its output is new-only and must be retained with the arm authority descriptor.

An existing parent-side monitor can wait for the authority file, independently
record its SHA and invoke this exact helper. The helper performs no metadata query,
source construction, native execution, policy selection or independently verified
promotion, and it never opens RESULT.json or any future source/outcome directory.

## Agent handoff

Send the independently prepared comparator agent:

- Canonical arm, authority and projected training-history paths and their parent
  recorded SHA256 values.
- Actual Python interpreter, cwd, and new outside-tree proposal/evidence directory.
- The immutable ARM itself and only the allowed exact contract source/test blobs.
- Explicit prohibition on RESULT.json, later warm/cold/ledger results, author repair
  head/patch, future protected outcomes beyond the released native baseline.

The agent will reason independently using the same original catalog, orders,
observations and full training profile evidence. Each submitted candidate must be
one exact catalog candidate object. It will execute the actual authenticated
`--agent-spec ... --candidate ... --out ...` CLI, at most eight proposals, including
independent native reexecution and every failure. It must retain the persistent
ARM_METER and may not republish/reset an exhausted meter.

The comparator transcript will retain timestamped prompts, concise proposal
rationales, exact command inputs and outputs, candidate hashes, native receipts,
failed attempts, and final meter. Hidden chain of thought is not recorded.
Model identity is the collaborating Codex agent; exact served model ID, token
pricing, and any unavailable tool/engineering cost remain UNKNOWN rather than
invented. No actual comparison is claimed until at least one proposal truly runs.

## Fixture verification

`RED.log` records eleven expected failures before the helper existed. `GREEN.log`
records all eleven source-free controls passing after implementation. Controls
cover exact current training profiles, contexts/episodes/receipts; excluded future
and other-binding attempt dereferences; training-baseline-only; missing future-arm
training evidence; wrong authority/metadata pins; altered CAS; wrong candidate
order; duplicate profiles; UNKNOWN preservation; and boolean native costs.

This input projection checks content hashes and retained probe lineage. Original
native receipts remain subject to their existing independent verifier authority.
The projection does not reverify native execution and grants no external effects.
