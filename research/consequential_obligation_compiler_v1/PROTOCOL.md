# Consequential Obligation Compiler V1 — pre-implementation protocol
Date: 2026-10-21. New candidate experiment, distinct from existing SQLite World Compiler #38820837059.

## Purpose
Test whether an independently supplied normative requirement together with live database schema authority compiles into a minimal *separating witness obligation*, without providing the needed observation set.

## Frozen requirement (independent of engine settings)
"Each declared foreign key in this schema must reject an orphan child insertion." Requirement version INTENT-FK-1. This is externally supplied policy, NOT inferred merely from schema existence.

## Test sources
Two controlled in-memory SQLite schemas; both have one INTEGER parent PRIMARY KEY and one child INTEGER foreign-key column, using distinct table/column names (parent/items and accounts/entries). This is synthetic controlled transfer, NOT previously unseen external source. Each executes foreign_keys ON and OFF, without disclosing the mode to the witness constructor. Authoritative schema metadata is PRAGMA foreign_key_list + table_info. Any policy change or schema inference deficiency -> UNKNOWN.
No other pre-seeded rows. No migrations or production data.

## Frozen operations & authority
Allowed: read sqlite_master and PRAGMA metadata; insert one orphan child row inside a transaction/savepoint then roll back; read database unchanged. No external file, network, DDL writes after frozen setup, no permanent mutation, no manual per-schema adapter.
Use source-derived names/columns rather than hard-coding particular SQL table names in the compiler. Construct a statement that an orphan insertion succeeds when FK enforcement is OFF and fails when ON. If the predicted separating witness cannot be compiled safely -> UNKNOWN.
Require native before/after total changes and row counts to match exactly.

## Comparison and costs
Full-information baseline: direct PRAGMA foreign_keys read, permitted to use the same policy, schema and engine. Independently run it, do not call selector superior if baseline is equally good/cheaper.
Cost: raw count of explicit sqlite.execute calls for discovery and testing (illustrative, NOT resource/time/economic cost). Label instrumentation limitations.
Independent oracle: direct PRAGMA foreign_keys plus native attempted violating insertion, separately replayed.
Protected consequence: decision AUTHORIZED_TO_TREAT_FK_REJECTION_AS_ENFORCED or REFUSE. Independent permission for real-world operations remains out of scope. Policy withdrawal => UNKNOWN, restored => native decision restored.

## Decisive results / stop
Native claim only within two in-memory SQLite fixtures and pinned Python version. No universal source semantics, no autonomous grammar invention, no R7.2 or CLC theorem re-proved or invoked. Prior bounded Lean evidence can be cited independently, not fused by prose.
If candidate fails to derive from metadata, record REJECTED or UNKNOWN. If baseline is cheaper, retain the negative. Avoid new source after outcome.
