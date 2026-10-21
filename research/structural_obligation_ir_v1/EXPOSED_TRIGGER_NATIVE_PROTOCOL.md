# Follow-on V1a: post-exposure trigger witness (NOT sealed third-source success)

After the sealed V1 run #39530686053 selected SQLite documentation paragraph 43 and returned IR_ONLY_UNSUPPORTED_NATIVE_OBLIGATION, this new experiment may independently check the already-exposed clause's native behavior. It is separate calibration, not a retroactive repair or promotion of unchanged V1 third-source witness.

Target, now EXPOSED: 'UPDATE OF column-name' trigger fires only when named column appears on SET left-hand side. SQLite native in-memory rows and audit table; two operations UPDATE y, UPDATE x; verify only second increments audit. Preserve original source bytes in PR and rollback check. Any mismatches REFUTE the constructed witness; don't change selected text after outcome. Comparator: informed developer can perform same native test, no advantage.
