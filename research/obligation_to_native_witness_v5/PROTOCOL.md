# V5 frozen requirement-to-native-witness compiler — prospective seventh source

DATE 2026-10-21. PRE-SOURCE LOCK: official independent SQLite https://www.sqlite.org/withoutrowid.html. Do not inspect its page before freezing this protocol AND algorithm. No replacement page on failure.

Target protected decision: Does a WITHOUT ROWID table require declaration of a primary key? Do NOT supply yes/no label, actual wording or target-specific test SQL as runtime compiler inputs. The question selects the source and keywords only.

## Architecture, frozen
1. Exact existing V4 deontic extractor, from research/deontic_obligation_v4/experiment.py at prior head 3b82a14cf83c0818a0fd424a10443efcd53af4b8 (unchanged).
2. Rank source-span-backed extracted obligations by overlap with question terms (without, rowid, table, primary, key). Require >=2 different terms and explicit REQUIRED modality. Selecting a lexical match does not establish meaning; independent relevance adjudication afterwards.
3. CLOSED generic SQL observation library, developed only from EXPOSED examples: nullable vs not-null field, explicitly typed vs untyped field, presence/absence of PRIMARY KEY in CREATE TABLE, plus generic optional CREATE TABLE table modifier token. The modifier token is obtained from question words, not from a hard-coded outcome label; currently allowed modifier is exactly SQL 'WITHOUT ROWID' because that syntax is public and preregistered in the protected *question*, not learned from source prose. This is an anticipated syntactic adapter, not an invented observation type.
4. If source IR says "must [have/specify/include] a primary key", compile a baseline valid schema and a single mutation removing the required PRIMARY KEY while retaining declared mode. If IR does not match this generic declarative form, abstain UNKNOWN_UNSUPPORTED_WITNESS. Source text must remain anchored, read-only, exact SHA recorded; no web SQL executed directly.
5. Execute in-memory native SQLite DDL, require rejected missing-key and accepted with-key; native SQLite is empirical oracle. No persistent effects; leave DB clean and report table names via sqlite_master.

## Baselines and claims
Strong full-information conventional engineer is allowed the same source and primitives. Expected baseline can choose missing-key CREATE TABLE directly. A coded equal-information ruleset and operation count comparison may tie; a human evaluation is UNMEASURED. No superiority claim.
A direct semantic rule preprogrammed as 'primary key required' is NOT spontaneous semantic-type invention. A success would show bounded compilation of newly source-extracted required-schema syntax to a generic existing DDL mutation.
This is a seventh SQLite-family prospective test, not a new programming language or MathGraph production runtime. R7.2, CLC and MathGraph Check stay unmodified and are not invoked.
STOP if source missing, source clause not relevant, no explicit REQUIRED primary key, unsafe modifier, no native evidence or no independent adjudication. No postexposure retuning.
