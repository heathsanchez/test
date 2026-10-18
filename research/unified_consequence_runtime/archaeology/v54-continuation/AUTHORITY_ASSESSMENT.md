# Authority separation assessment

Read-only source review, 2026-10-15. No exploit demonstration, mutation, or verification execution performed. Observed UDM HEAD `10269fa87dacd47b7d0036935bc8b006e5041adc`. SHA256s: `v54_runtime.py ec14ac266225e3a3d19740294d1ec587690037cd9357cb00fd839cb14310fb5a`; `developmental_machine.py 04871accdcd3777c10671e9dc572eb556a5e9885cd8c3e5fb3a0be7686bec955`; `v54_source.py adda0919fe17eff04646bd217620a6adfc66ef0dd9418e1663e850ed09857892`; `v54_verify.py c40a4e1f227ea83b82ceb8fd4a404cf85fd04ced3b87657934c0c92fb72f0456`.

## Conclusion

Scientific capability admission is separated from a declared local user action authority ceiling. The mediated routes contain genuine scope, source, receipt, and causal-support checks. **Nonbypassability is UNKNOWN.** No airtight reference-monitor or external-action authorization claim is warranted. This matches `v54_runtime.py:3`, which explicitly says the module mediates its own local routes and is not a nonbypassable sandbox, and `v54_runtime.py:34`, whose ceiling records `UNKNOWN_NONBYPASSABILITY`.

## Scientific admission

`developmental_machine.py:3-4` distinguishes FLASH dependency closure from empirical verification. `Machine.admit` at 244 validates transition and frozen task, invokes pinned producer and independent verifier at 247–249, requires accepted status plus score1 at 250–253, and only then appends support, native-verification evidence and an executable capability at 255–266. Archived observation/program hashes and frozen-task digest gates are enforced by `safe_task` 45–50 and `run_source` 189–197. The declared capability scope at 260–265 remains local research over the original archived snapshot.

V54 adds stricter operator-specific admission. `v54_runtime.py:62–75` requires the source session's acquired O1/O2, exact dependency shape, live O1 parent for O2 and independent native verification before retention. `independent_verify` 44–60 starts a separate Python process, supplies only program/stage/source/world paths, and checks the newly generated receipt's exact binding. Admission appends separate support, verification evidence and capability nodes at 78–89. A candidate or prose claim alone is not accepted.

`v54_verify.py:80–115` restricts stage, operator count, token-rewrite syntax and `if` scope. Source authentication is at 62–67. It reconstructs pinned native worlds from Git archives at 140–165 and 340–348, ignoring producer worktree contents. Native tests are constrained to exact declared command/cwd matches at 262–265. Their runner uses an isolated Python import mode and cleaned environment at 276–280, records imported source hashes, requires source unchanged and imports valid at 284–300, and only accepts all measured gates plus source restoration at 425–429. `_write_receipt` 308–314 creates a new file, hashes its contents and marks it read-only. `receipt_binding_valid` 317–323 checks exact program/stage/scope/source/status bindings; its docstring explicitly requires native admission to rerun verification.

These establish bounded scientific admission behavior for these routes. The receipt hash provides integrity binding, not an independently authenticated authority signature.

## User action authority

`v54_runtime.py:32–37` declares an independent user research mission, local pinned worktree/native-test effects, and no external effects, then makes that ceiling a premise of the supplied constructor node. Capability acquisition carries the same ceiling and `LOCAL_RESEARCH_EXECUTION_ONLY` at 78–79. `apply` 93–105 checks live causal support, executable class/source, exact target scope and equality with the current authority ceiling before calling the source effect. Capability acquisition therefore does not itself grant broader rights along this route.

This descriptor is a local policy ceiling derived from session authorization. It is not user identity authentication, an external application's permission grant, an OS/network sandbox, or proof that every potential effect passes through this method. Scientific success does not authorize contacting services or altering third-party state.

## Genuine route guards

- `v54_runtime.py:40–42`: both Metatron and FLASH must report a node live. Parent liveness is checked before and after native verification at 67–75; consequence liveness is checked before and after verification at 128–135.
- `v54_runtime.py:93–105`: type/source, target scope and ceiling gates precede operator execution.
- `developmental_machine.py:281–293`: frozen task, capability scope and causal-support gates precede producer execution; resulting consequence must independently verify.
- `v54_source.py:59–78`: source bytes must match the pinned original program. `OriginalV54.__init__` 158–176 restricts exact three distinct pinned worlds, operational timeout ceiling, and output placement outside resettable worlds.
- `v54_source.py:309–345`: warm preparation requires acquired O1; apply requires an acquired operator, exact learned scope, expected line first word and exactly one source token; warm search requires warm preparation and preceding O1 effect.

## Limits and trusted surfaces

The code runs in ordinary Python with trusted host filesystem/process access. `Machine.log`, paths and configuration are regular instance attributes (`developmental_machine.py:69–99`), while `append` 116–119 accepts caller-supplied node kind/payload/premises. The content-addressed store verifies its own data bindings at 101–114 but is not a separate principal or protected storage service.

The source adapter exposes the mutable session namespace at `v54_source.py:184–186`; pinned source execution uses `exec` at 97–98/205–211. `OriginalV54.apply_operator` at 319 checks source acquisition/scope but has no Machine/FLASH liveness argument. Its direct effect methods, `execute_native` 356 and source-phase execution interface are callable independently of `V54Runtime.apply`; therefore the runtime's guarantees apply to its mediated route, assuming callers respect that boundary. `_ObservedSubprocess.__getattr__` at 107–108 delegates to the ordinary subprocess module; the observation wrapper is operational accounting/timeout management, not a comprehensive external-effect monitor.

`restore_session` at `v54_runtime.py:139–147` intentionally reconstructs source session state from live warranted capabilities; it is trusted in-process restoration, not a tamperproof import boundary. `Machine.run_source` 189 and the independent verifier entrypoint are public callable APIs whose scientific scope checks do not themselves establish user action authority.

No direct-call or mutable-state exploit was attempted. No conclusion is drawn about exploitability under an attacker model. The supported statement is bounded route enforcement plus transparent scientific authority separation. The whole-process, all-effects, nonbypassable boundary remains **UNKNOWN**.
