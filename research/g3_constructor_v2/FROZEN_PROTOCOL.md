# G3 constructor inhabitation V2 — frozen design, 2026-10-30

Status: CANDIDATE DESIGN, no result or strict G3 promotion.

## Residual from V1
Preregistered G3 run 40983573858 returned UNKNOWN_ADAPTER on duplicated hidden receiver signatures; generic public-constructor embedding repair then produced a source-native candidate on go-cache (40983814078), but fair manual time-aware baseline tied. The untouched V1 failed to admit rank-2 allegro/bigcache@6e72b805b2b3f6d7952ac172f6c8f7aefecfc00e (40986803131), because it only knows constructors taking two time.Duration arguments. Preserve all negative lineage and source pins.

## V2 experiment, before target source inspection
Freeze next metadata rank-3 repository `dgraph-io/ristretto` at `a56a38ebeec716a0da3d20a46b417ca2ab7c81f4`, obtained via Git ref (no source/README/issues/PRs/commit titles inspected). No target-specific adapters or post-source selection.

Task: synthesize a *constructible candidate* from non-test Go AST, then compile and call it in a native Go process. This is constructor/input inhabitation, not new operation invention.

Predeclared inhabitant grammar:
- scalar int/uint/float -> 1; string -> "x"; bool -> false; time.Duration -> 80*time.Millisecond; context.Context -> context.Background(); []byte -> []byte("x");
- same-package exported struct T -> pkg.T{} (or pointer), unless a single unambiguous exported function returning T and inhabitable parameters can be used as a default-constructor helper; prefer that helper;
- generic type arguments -> [string,...], one per generic parameter, only as speculative candidate under declared constraints;
- funcs/channels/opaque/ambiguous/cyclic forms -> UNKNOWN, never arbitrary fabricated values.
- exported constructors returning *T or (*T,error); one minimally costly viable root is selectable, ties UNKNOWN.
- compile native generated code and call constructor; if compiler rejects or constructor returns error, fail as UNKNOWN_NATIVE_CONSTRUCTION, not a source defect.

Controls:
1. Synthetic fixtures cover 2x duration, context+config/default helper, integer-only factory, generic config, unreachable/function-typed arguments, and ambiguous constructors.
2. Watch new tests fail on V2 stub before implementing semantics (TDD).
3. Freeze tool and test source SHAs before the first rank-3 source read.
4. Fair baseline: a simple signature enumeration plus manually specified constructor argument recipe receives the same native compile/call opportunity; no superiority claim without causal ablation.
5. V2 may be warranted only within actual compiled/verified fixture/source boundary. Strict G3 stays UNKNOWN because the inhabitant grammar is predefined, even if cold target construction succeeds.

No modifications to V1's historical source or V45 pool; no upstream messages, issues or PRs.
