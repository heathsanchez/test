#!/usr/bin/env python3
"""STRICT type declaration native check; explicitly POST-EXPOSURE only."""
import json,sqlite3
from pathlib import Path
db=sqlite3.connect(":memory:")
try:
 before=db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
 try:
  db.execute("CREATE TABLE invalid_type(column_without_type) STRICT")
  missing="ACCEPTED"
 except sqlite3.OperationalError:
  missing="REJECTED"
 after_bad=db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
 db.execute("CREATE TABLE typed(column_with_type INT) STRICT")
 typed="ACCEPTED" if db.execute("SELECT name FROM sqlite_master WHERE name='typed'").fetchone() else "MISSING"
 assert missing=="REJECTED" and typed=="ACCEPTED" and before==after_bad
 out={"status":"WARRANTED_POSTEXPOSURE_NATIVE_STRICT_WITNESS",
      "missing_type":missing,"specified_type":typed,"failed_ddl_preserves_schema":before==after_bad,
      "sixth_source_prospective_witness":"UNKNOWN_UNSUPPORTED_PREEXPOSURE"}
 Path(__file__).with_name("exposed_native_result.json").write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps(out,sort_keys=True))
finally: db.close()
