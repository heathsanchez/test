# Contextual record telescopes

Candidate f08aea2a99d1955a825d53d4dc21a542367978d3 extends semantic base113e3155.
Qualification run36832195307 SUCCESS; artifact11147733147 (167174 bytes),
SHA256609ebf49c2a45ce49dfa376a3b1a352566101158f043439220ddbb01edaaae0b.
Current194:110A/60R/24U; frozen193:108A/61R/24U. Zero wrong/errors/regressions.
Five prefixes,13 execution witnesses and renamedPProd pass independent references
and removal/restoration. No whole-file gain.

## Checked law

One safe, nonrecursive, nonindexed Type record; one constructor and recursor;
1..4 parameters, 0..5 fields, at most three inductive universes. Bounds select
work. Acceptance requires the complete obligation list:

1. Validate ownership, universe uniqueness, constructor result and recursor metadata.
2. Infer each parameter annotation as a type in its actual validated prefix.
3. Prove constructor and recursor parameter annotations convertible in that prefix.
4. Infer every field type in the parameter/preceding-field context. Exclude self
   reference. Prove max(field universe, result universe) = result universe.
5. Validate motive, minor, major, result, constructor argument order and rule body.
6. Check EVERY rule parameter annotation is a type before contextual conversion;
   remaining rule annotations are the validated expressions with checked shifts.
7. Promote signatures, then install checked projections and recursor reduction.

GetElem? exposes outParam T versus T; the existing conversion checker proves
that equality. The implementation contains no family-name admission rule.

## Iterations and failed lineage

- 05b21a0d / run36830221318: three target prefixes RED, negative controls pass.
- f0c7b019 / run36830935857: compiled, but extended an unparameterized-record
  scope boundary. Restricted this iteration to parameterized records in33fc5d79.
- 33fc5d79 / run36831073766: historical renamed-PProd UNKNOWN expectation exposed.
  New law earns this fixture; preserve historical oracle and require independent
  acceptance rather than silently freezing UNKNOWN forever.
- e8b32a6b / run36831329600: all semantic checks and387 replay passed, zero final
  gains. Artifact upload failed because a filename contained '?'. Do not call
  the overall run successful. Filenames were sanitized in f08aea2a.
- Fresh review found a missing sort premise for rule parameter annotations.
  Fixed in56137bd; reviewer confirmed static closure. The earlier e8 candidate
  is not promoted despite its green semantic replay.
- 527fca82 / run36831891222: Applicative and Monad successor prefixes RED.
- f08aea2a: identical checked law extended from3 to5 fields; Applicative and
  Monad prefixes plus every Applicative projection and recursor witness pass
  locally using the exact hosted binary. Full hosted qualification passed as reported above.

## Dependency propagation

GetElem? x2 advances to Nat.decEq.match_1. Functor -> Applicative -> Monad
also advances fueled-chain to Nat.decEq.match_1. The pair-list files already
stop there. Five whole files therefore share the same next typing obligation.
This is dependency closure, not five independent new conversion problems.

## Boundary

No large-corpus or leaderboard instruction-performance qualification. No Arena
submission. No reference checker is called by the Nucleus runtime. Independent
qualification uses pinned lazylean KAM/subst: two engines, one implementation lineage.
