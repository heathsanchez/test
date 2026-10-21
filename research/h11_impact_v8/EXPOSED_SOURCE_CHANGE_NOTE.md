# Source-exposure qualification note — retained alongside frozen protocol

The upstream file was read AFTER the original immutable protocol. It contains class ReceiveBuffer.__bool__ returning bool(len(self)). The concrete source edit is therefore selected AFTER seeing source, and is not a prospective novel change-transformation discovery.

Exact approved implementation rewrite for this study:
'        return bool(len(self))' -> '        return len(self) != 0' within class ReceiveBuffer.__bool__, one occurrence. The equivalence is conditioned on len(self) yielding a nonnegative Python length and ordinary Boolean contexts. Does not preserve introspection/tracing details.

Prospectively frozen test choices remain h11/tests/test_receivebuffer.py (owner) and h11/tests/test_headers.py (candidate). Source/test commits remain immutable. Independent coverage observer records __bool__ calls in each exact test process; no call in candidate suite is only a bounded dynamic non-observation condition. A trusted runtime envelope is explicitly assumed, not proven. Full app release unknown. Equal-info coverage baseline expected tie.

Introduce mutant changed __bool__ to return False; upstream owning test must fail. Introduce synthetic extra test in temporary copy of header suite that calls ReceiveBuffer.__bool__; coverage tracer must detect the new dependency and revoke its candidate skip. This is an *added* negative control on already exposed source, not a retrofit of the frozen rule.
