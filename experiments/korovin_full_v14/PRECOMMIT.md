# Korovin V14 — Blinded Human Mathematical Usefulness Study

This protocol is frozen before recruiting or exposing any participant to a study packet.

## Question

Do independently recruited mathematically competent humans solve and understand protected problems more effectively when given the machine-invented verified object than when given either the raw transformation description or a size-matched sham abstraction?

This is the direct test of the remaining Korovin criterion: usefulness to human mathematicians.

## Source worlds

Use exactly the three V10 residual-bearing worlds already frozen throughout V11–V13:
- world 4: 25 reachable states;
- world 5: 79 reachable states;
- world 11: 43 reachable states.

No world replacement is permitted.

## Conditions

### RAW
Participants receive the two primitive transformations on the 4-point carrier, composition convention, and task instructions. They do not receive the canonical object, state graph, or learned equations.

### OBJECT
Participants receive a human-facing package generated from the verified invented object:
- short definition of the canonical states as equivalence classes of words by induced action;
- canonical representatives;
- compact retained equations;
- complete state-by-generator transition structure, rendered as a lookup table;
- a one-paragraph explanation of how to use the representation.
They do not receive the original primitive transformation maps.

### SHAM
Participants receive a package matched to OBJECT in format, approximate symbol count, number of states, and table dimensions, but with deterministic randomized transitions. It is clearly described only as the supplied formal system; participants are not told that it is a control.

## Blinding and assignment

Minimum analyzable sample: 18 participants with university-level mathematics or theoretical computer-science training, or equivalent professional experience.

Within-subject Latin-square design. Each participant solves one source world under each condition, with world-condition assignment and presentation order balanced across participants. No participant sees the same world twice.

Participants are told that three different mathematical representations are being evaluated, not which condition is expected to perform best.

## Protected tasks per world

Each packet contains 12 scored tasks generated from the frozen root `KOROVIN_V14_HUMAN_USE_2026-08-22`:
- 3 word-equivalence decisions;
- 3 canonical/shortest-representative problems;
- 2 composition prediction problems;
- 2 derive-or-refute proposed equalities;
- 1 explain a nontrivial equality in the supplied representation;
- 1 free structural question: state one non-obvious reusable regularity and demonstrate it on a new example.

All objective tasks are generated after this precommit and have externally machine-checkable answer keys. Free/explanation tasks are graded blind to condition by a frozen rubric assessing correctness, use of reusable structure, and whether the explanation generalizes beyond the single instance.

## Time and interaction

Maximum 20 minutes per packet. Participants record start/end timestamps. Calculator and scratch paper are allowed; external AI, CAS, code execution, and web search are not allowed.

## Primary endpoints

Per participant-condition:
- objective accuracy;
- median seconds per correct objective answer;
- number correct within 20 minutes.

## Secondary endpoints

- explanation score (0–4 frozen rubric);
- reusable-regularity score (0–4 frozen rubric);
- self-reported confidence after each task (1–5), used only as a secondary descriptive measure.

## Frozen success gates

G0: at least 18 analyzable participants and balanced Latin-square completion.
G1: OBJECT objective accuracy exceeds RAW by >= 10 percentage points.
G2: OBJECT objective accuracy exceeds SHAM by >= 20 percentage points.
G3: OBJECT median time per correct objective answer is <= 0.70 × RAW.
G4: OBJECT median time per correct objective answer is <= 0.60 × SHAM.
G5: OBJECT median explanation score exceeds RAW by >= 1 rubric point.
G6: OBJECT median reusable-regularity score exceeds RAW by >= 1 rubric point.
G7: no OBJECT world has lower objective accuracy than both RAW and SHAM in its balanced assignments.
G8: all machine-checkable answer keys reproduce independently before scoring participant responses.

For transparency, raw per-participant anonymized scores and all exclusions must be reported. Failure of any gate is retained as the evidentiary result; no post-hoc threshold change is allowed.

## Claim boundary

A pass would provide direct evidence that, in these finite formal worlds, machine-invented verified mathematical objects are useful to mathematically trained humans for solving, explaining, and extracting reusable structure. It would still not establish historical-level mathematical novelty such as invention of groups, sheaves, or perfectoid spaces.
