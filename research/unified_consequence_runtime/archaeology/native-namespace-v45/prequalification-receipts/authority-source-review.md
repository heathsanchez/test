# Independent V45 authority source review

Scope: read-only review of the V45 implementation against the independently sealed
control requirements and acceptance matrix. No repository code was imported or
executed, no Git/index operation was performed, and no scientific task was queried.
This document is source analysis, not independent native qualification.

## Concrete findings sent to owners

1. **Forged `__func__` bypassed actual outer callable binding.** The first V45
   bootstrap removed recursive `__wrapped__` lookup but inherited arbitrary
   `getattr(obj, '__func__', obj)` from the V2 fingerprint wrapper. A B03 decorator
   can instead assign `wrapper.__func__ = original`; the no-op wrapper then hashes
   as the original failing assertion. Sent to the worker owner and root. The owner
   reports actual RED and a fix that recognizes native callable types.
2. **`isinstance` remains spoofable at the new callable-type boundary.** The first
   fix used `isinstance(obj, types.FunctionType/MethodType)`. An arbitrary callable
   instance can supply a `__class__` property that returns either built-in type,
   together with forged `__code__` or `__func__`. Exact native types are required
   here because functions and bound methods cannot be subclassed. Sent exact
   follow-up to the worker owner and root. A subsequent source re-read confirms
   exact `type(obj) is types.MethodType` and `type(obj) is types.FunctionType`
   checks; this closes both reported outer identity paths by source inspection.
   Regression execution remains the implementer's separate evidence.
3. **Wildcard shadowing inventory omitted Python binders.** The initial
   `_module_bindings` omitted exception-handler and structural-pattern string
   capture names, and returned before scanning definition-time defaults,
   annotations, decorators, bases and class keyword expressions. For example,
   `match 0: case ANSWER: pass` or `def helper(x=(ANSWER := 0)): pass` could shadow
   an imported `ANSWER` without colliding with the recorded namespace. An explicit
   class-body `global ANSWER; ANSWER = 0` likewise escapes ordinary class-local
   scoping. The current source conservatively inventories these binders. The
   static owner reports actual RED and 78 passing static controls. I re-read the
   fix; no remaining concrete bypass found in that bounded collector.
4. **Compiler accounting schema mismatched the actual worker.** The qualifier
   required `attempts/calls` while the actual worker exposes
   `compilation_calls/compilation_seconds/records`. Every genuine qualification
   would have refused. The driver owner reports RED followed by a genuine
   snapshot-shaped regression and correction.
5. **The seal checked fixture bytes but omitted frozen Git modes.** A fixture
   chmod can survive byte hashes and be copied into a different typed Git tree.
   The current qualifier checks the mode recorded in the independently sealed
   fixture index. The driver owner reports an actual chmod RED and correction.

Static source re-read authenticated
`native_admission_v45.py` SHA256
`d1cb37479f91d0f0afaaffc61154aba7a0aff45ef7389251b556b63d87bf1677`.

## Verification gaps and warrant limit

The original V2 adversarial tests preserve original regressions but do not alone
exercise the new V45 private bindings. I requested explicit V45 mapping/execution
of R01--R18, particularly parameter deselection, missing call reports, resealed
receipts, environment/plugin replacement, recollection/execution order mismatch,
and postcollection outer-code replacement. The root and worker owner are adding
that mapping before the stable whole-suite run.

The qualifier's raw packet audit reconstructs original native status and packet
consistency. It does not independently establish original declaration identity.
The downloaded CI artifact still needs a separate audit: authenticate exact frozen
source, original declaration/C3 origins, native interpreter/package identity, and
compile original raw/pytest-rewritten declarations without executing source to
compare every protected actual outer-code observation. No native admission or
G2--G6 claim follows from this source review; all scientific gates remain UNKNOWN.
