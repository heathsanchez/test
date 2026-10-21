#!/usr/bin/env python3
"""Bounded source-to-witness compilation on native sqlite3; no general semantic authority."""
import json
import sqlite3
from pathlib import Path

POLICY = {"id": "INTENT-FK-1", "obligation": "reject_orphan_inserts"}
SCHEMAS = {
    "items": (
        'CREATE TABLE parent (id INTEGER PRIMARY KEY)',
        'CREATE TABLE items (id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL REFERENCES parent(id))'
    ),
    "entries": (
        'CREATE TABLE accounts (account_key INTEGER PRIMARY KEY)',
        'CREATE TABLE entries (entry_key INTEGER PRIMARY KEY, account_ref INTEGER NOT NULL REFERENCES accounts(account_key))'
    )
}
def ident(value):
    if not value or not all(c.isalnum() or c == "_" for c in value):
        raise ValueError("unsafe identifier")
    return '"' + value.replace('"', '""') + '"'
def sql(conn, statement):
    sql.calls += 1
    return conn.execute(statement)
sql.calls = 0
def compile_obligation(conn, policy):
    """Derive an executable experiment, not an authoritative general theorem."""
    if policy is None:
        return {"status":"UNKNOWN_WITHDRAWN_POLICY"}
    if policy.get("obligation") != "reject_orphan_inserts":
        return {"status":"UNKNOWN_UNSUPPORTED_POLICY"}
    tables = [r[0] for r in sql(conn, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    candidates = []
    for table in tables:
        fk = sql(conn, "PRAGMA foreign_key_list(" + ident(table) + ")").fetchall()
        for row in fk:
            candidates.append((table,row))
    if len(candidates) != 1:
        return {"status":"UNKNOWN_AMBIGUOUS_FK_COUNT", "count":len(candidates)}
    child, fk = candidates[0]
    # Native PRAGMA layout: id, seq, table, from, to, on_update, on_delete, match.
    if fk[1] != 0 or not fk[3]:
        return {"status":"UNKNOWN_COMPLEX_FK"}
    columns = sql(conn, "PRAGMA table_info(" + ident(child) + ")").fetchall()
    by_name = {x[1]:x for x in columns}
    col = by_name.get(fk[3])
    other_required = [c for c in columns if c[3] and not c[4] and c[1] != fk[3] and c[2].upper() != "INTEGER"]
    if col is None or "INT" not in col[2].upper() or other_required:
        return {"status":"UNKNOWN_INADMISSIBLE_SCHEMA"}
    parent = fk[2]
    pcols = sql(conn,"PRAGMA table_info(" + ident(parent) + ")").fetchall()
    if not any(c[1]==fk[4] and "INT" in c[2].upper() for c in pcols):
        return {"status":"UNKNOWN_PARENT_TYPE"}
    sentinel = 987654321
    exists=sql(conn, "SELECT 1 FROM " + ident(parent) + " WHERE " + ident(fk[4]) + " = " + str(sentinel) + " LIMIT 1").fetchone()
    if exists is not None:
        return {"status":"UNKNOWN_SENTINEL_COLLISION"}
    return {"status":"ADMISSIBLE_WITNESS", "child":child, "column":fk[3], "parent":parent,
            "sql":"INSERT INTO " + ident(child) + " (" + ident(fk[3]) + ") VALUES (" + str(sentinel) + ")"}
def execute_witness(conn, candidate):
    if candidate["status"]!="ADMISSIBLE_WITNESS":
        return {"status":"UNKNOWN_NO_ADMISSIBLE_WITNESS"}
    child=ident(candidate["child"])
    before=sql(conn,"SELECT COUNT(*) FROM "+child).fetchone()[0]
    sql(conn,"SAVEPOINT qualified_probe")
    try:
        sql(conn,candidate["sql"])
        observation="ACCEPTED_ORPHAN"
    except sqlite3.IntegrityError:
        observation="REJECTED_ORPHAN"
    finally:
        sql(conn,"ROLLBACK TO SAVEPOINT qualified_probe")
        sql(conn,"RELEASE SAVEPOINT qualified_probe")
    after=sql(conn,"SELECT COUNT(*) FROM "+child).fetchone()[0]
    assert before==after, "probe changed source"
    return {"status":observation,"state_preserved":before==after}
def baseline(conn):
    return sql(conn,"PRAGMA foreign_keys").fetchone()[0]
def independent_oracle(conn, candidate):
    # Independently read configuration; this is not proof of all possible future executions.
    configuration=baseline(conn)
    expected="REJECTED_ORPHAN" if configuration else "ACCEPTED_ORPHAN"
    return configuration,expected
def trial(schema_name,setting):
    conn=sqlite3.connect(":memory:")
    sql.calls=0
    try:
        sql(conn,"PRAGMA foreign_keys="+str(setting))
        for statement in SCHEMAS[schema_name]:
            sql(conn,statement)
        discovery_start=sql.calls
        candidate=compile_obligation(conn,POLICY)
        candidate_cost=sql.calls-discovery_start
        assert candidate["status"]=="ADMISSIBLE_WITNESS",candidate
        start=sql.calls
        observed=execute_witness(conn,candidate)
        candidate_cost+=sql.calls-start
        start=sql.calls
        conf,expected=independent_oracle(conn,candidate)
        baseline_cost=sql.calls-start
        assert observed["status"]==expected
        assert conf==setting
        no_policy=compile_obligation(conn,None)
        assert no_policy["status"]=="UNKNOWN_WITHDRAWN_POLICY"
        restored=compile_obligation(conn,POLICY)
        assert restored==candidate
        return {"schema":schema_name,"configuration":setting,
                "compiled":candidate,"native_observation":observed,
                "oracle_configuration":conf,"candidate_sql_calls":candidate_cost,
                "baseline_sql_calls":baseline_cost,"withdraw":"UNKNOWN","restore":"PASS",
                "global_intent_warrant":"UNKNOWN_WITHOUT_INDEPENDENT_GENERAL_PROOF",
                "comparative_result":"BASELINE_CHEAPER"}
    finally:
        conn.close()
def main():
    runs=[trial(name,setting) for name in SCHEMAS for setting in (0,1)]
    assert len(runs)==4 and all(x["candidate_sql_calls"] > x["baseline_sql_calls"] for x in runs)
    out={"scope":"two controlled in-memory SQLite schemas, not unseen external native sources",
         "cases":runs, "status":"WARRANTED_BOUNDED_NATIVE_WITNESS_COMPILATION",
         "advantage":"REJECTED_COST_ADVANTAGE_VS_FULL_INFO_PRAGMA_BASELINE",
         "R7_CLC_MATHGRAPH":"referenced verified prior mechanisms; not invoked in this experiment"}
    Path(__file__).with_name("result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":out["status"],"cases":len(runs),"observations":[x["native_observation"]["status"] for x in runs],
       "candidate_costs":[x["candidate_sql_calls"] for x in runs],
       "baseline_costs":[x["baseline_sql_calls"] for x in runs],
       "comparison":out["advantage"]},sort_keys=True))
if __name__=="__main__": main()
