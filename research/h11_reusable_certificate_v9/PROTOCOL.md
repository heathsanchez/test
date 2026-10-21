# V9 reusable, change-family-scoped H11 impact certificate — frozen before evaluation

Source authority: python-hyper/h11@62c5068c971579d61fa1b55373390e12f25fd856. Protected target h11/_receivebuffer.py::ReceiveBuffer.__bool__, independent actual suite h11/tests/test_headers.py, owning suite h11/tests/test_receivebuffer.py.
Previous V8 [native CI #39687187080] observed 0 changed-method calls in headers, 5 in owner, and an injected call triggered 1. This is only session evidence, not itself a proof.

## Crucial package import observation
The headers test runs under h11 package initialization, which imports other modules including _connection, which references _receivebuffer. So "no import of changed module" is false. New proposed reuse certificate is about function *invocation* under exact source and execution assumptions, not import independence. Fail closed on changes to module top-level, class signature, __bool__ decorator/annotations, reflected code objects, test imports or qualified call graph.

## Fixed reused certificate and accepted future edits
V9 independently inspects Python AST and hashes source/test identities. It admits a future change only when EXACTLY ReceiveBuffer.__bool__ return expression differs, all other module AST nodes and source outside that expression remain byte-identical, and the change belongs to declared finite controlled grammar:
 A: return len(self) != 0
 B: return bool(self._data)
 C: return len(self._data) > 0
 D (deliberately behavior-changing): return False
 D may be *outside behavior-preserving class*, but the reuse certificate must not claim protected __bool__ behavior preserved. Independent owning-suite regression must detect D. The only proposed omission is headers test on a pinned session, not omitted from all product release. It is not a generalized independently discovered grammar.

## Certificate invalidation / negative
 Inject source-level call to ReceiveBuffer.__bool__ in a temporary copy of header test; invalidate exact suite hash and deny reuse, then prove runner traces at least one call.
 Inject new top-level call to ReceiveBuffer.__bool__ in module or import dependency; deny reuse before running.
 Change a non-__bool__ function; deny reuse.
 Tamper certificate source digest; deny reuse.
 Include an alternative behavior-changing __bool__ edit D: selecting headers alone is no proof of target behavior, ensure owning suite has to run and fails. Never elevate a failed owning suite to review permission.

## Comparator and measurements
Run the original candidate V8-style full+selected native tests once for baseline, then all 4 future edits. For each edit run owner tests and full tests for scientific qualification; skip decision can be simulated only when source/test identity and static checks pass. Independent conventional *cached coverage* selector receives the same initial V8 zero-call observation and exact source/test version data and makes the SAME skip. Include certificate acquisition, checker execution, owner tests, independent negative controls and full-test audit in total cost. Speedup only hypothetical test-process saved, never realized in experiment. Full application/release remains UNKNOWN. MathGraph/R7.2/CLC unchanged.

## Stopping
Reject if import closure/reflection cannot be certified; state dependence on exact Python runner environment and pinned source. A native trace cannot warrant universal absence of effects. A reviewer cannot call this proof of general Python noninterference or higher capability than conventional coverage caching.
