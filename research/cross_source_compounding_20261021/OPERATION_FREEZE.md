# Source-obstruction-derived verification operation: freeze before next source

Source A: go-ini/ini@e2db55b0e088fa4ee0c128aa4ade263cdc1d7f08.
Native witness: trailing backslash stripped after serialization, independent CI 39540390818.

Operation to transfer: boundary-sensitive *semantic drift localization*. Given a source serializer and parser:
1. Generate bounded perturbations of semantically sensitive suffix characters.
2. Trace x -> encoded1 -> decoded1 -> encoded2 -> decoded2.
3. If changed, report the earliest transition at which semantics drift, and verify a literal independent witness plus unchanged control.
4. Report UNKNOWN when no witness found. Never label drift an upstream bug without contract authority.

Target B is source-blind: BurntSushi/toml@d733fc535e4a9f3c454e421a87b90ade5d49bf31; no source or tests inspected AFTER this freeze (earlier public README and prior GEN1 adapter were already exposed, so this is NOT a fully unopened/novel transfer).
Inputs: retained nine-string corpus and fixed perturbations (# ; = space quote backslash CR LF) exactly as previous Gen3; no new per-target winning primitive. B native adapters may use only prior known public API.
Strong baseline: same source, prior known adapter, operation specification, generators and execution budget; can copy and reuse this procedure. Thus a tie is expected absent a new efficiency result.
Charge observable native process and compilation time, setup and candidate calls. Human design and adaptation MUST be explicitly marked uncharged. No commercial / prospective-blind claim.

Pass gate: source-native trace with independent compare; tested boundary cases do not falsify verifier correctness; equal-information baseline truly run. Exclusive compounding requires net saved acquisition across new separate targets including method acquisition, and is NOT implied by this experiment.
