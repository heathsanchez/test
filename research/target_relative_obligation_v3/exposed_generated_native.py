#!/usr/bin/env python3
"""Explicitly POST-EXPOSURE witness; not prospective source-to-obligation success."""
import sqlite3,json
from pathlib import Path
db=sqlite3.connect(":memory:")
db.execute("CREATE TABLE t(a INTEGER,b INTEGER GENERATED ALWAYS AS (a*2) VIRTUAL)")
db.execute("SAVEPOINT trial")
out={}
for name,sql in [
 ("direct_insert","INSERT INTO t(a,b) VALUES(4,8)"),
 ("direct_update","UPDATE t SET b=8")]:
 try:
  db.execute(sql)
  out[name]="ACCEPTED"
 except sqlite3.OperationalError:
  out[name]="REJECTED"
db.execute("INSERT INTO t(a) VALUES(4)")
out["derived"]=db.execute("SELECT a,b FROM t").fetchall()
db.execute("ROLLBACK TO trial");db.execute("RELEASE trial")
out["restored_empty"]=db.execute("SELECT COUNT(*) FROM t").fetchone()[0]==0
assert out=={"direct_insert":"REJECTED","direct_update":"REJECTED",
             "derived":[(4,8)],"restored_empty":True},out
out["boundary"]="WARRANTED_EXPOSED_ONLY_POSTHOC_WITNESS"
out["prospective_obligation_capture"]="NOT_ESTABLISHED_V3_FALSE_TARGET"
Path(__file__).with_name("exposed_native_result.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out))
