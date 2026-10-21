#!/usr/bin/env python3
"""Post-exposure native SQLite trigger test. NOT held-out method transfer."""
import sqlite3,json
from pathlib import Path
conn=sqlite3.connect(":memory:")
conn.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, x INT, y INT)")
conn.execute("CREATE TABLE audit(marker TEXT)")
conn.execute("CREATE TRIGGER trig AFTER UPDATE OF x ON t BEGIN INSERT INTO audit VALUES('x_updated'); END")
conn.execute("INSERT INTO t VALUES(1,10,20)")
conn.commit()
conn.execute("SAVEPOINT p")
conn.execute("UPDATE t SET y=21 WHERE id=1")
not_target=conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
conn.execute("UPDATE t SET x=11 WHERE id=1")
target=conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
conn.execute("ROLLBACK TO p");conn.execute("RELEASE p")
restored=conn.execute("SELECT x,y FROM t WHERE id=1").fetchone()==(10,20)
empty=conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]==0
assert (not_target,target,restored,empty)==(0,1,True,True)
r={"experiment":"POST_EXPOSURE_TRIGGER_WITNESS","not_target_column_audit":not_target,
"target_column_audit":target,"rollback_exact":restored and empty,
"verdict":"NATIVE_WITNESS_PASS_EXPOSED_ONLY","prospective_third_source_claim":"UNCHANGED_UNKNOWN_UNSUPPORTED_WITNESS"}
Path(__file__).with_name("exposed_trigger_result.json").write_text(json.dumps(r,indent=2)+"\n")
print(json.dumps(r,sort_keys=True))
conn.close()
