# G6-001 Theorem Boundary and Portable-Spec Plan

**Goal:** Resolve the exact tutorial-012 residual with the least theorem
capability, strengthen exact-head qualification through tutorial 001-011, and
introduce a portable semantic specification that can state the theorem rule
without becoming a Rust API model.

**Architecture:** A theorem is parsed as a distinct declaration. Its declared
type must infer to `Prop` (`Sort 0`), and its proof is checked against that
type in the prior authority. Only then is a constant signature installed. The
proof body is discarded from the executable environment, so theorem constants
remain usable by type while never becoming delta-reduction fuel. The portable
Lean layer separately specifies syntax, prior-environment derivability, and
signature-only theorem installation.

## Frozen obstruction and falsifier

- Residual: `G6-001`, upstream tutorial case 012.
- Frozen bytes: `evidence/residuals/G6-001/fixture.ndjson`.
- Current result: `UNKNOWN`; required result: `REJECT`.
- Falsifier: the exact residual remains undecided, a valid theorem fails,
  self-reference is admitted, a proof body becomes a definition body, a
  malformed theorem reference is not a parse error, or any protected earlier
  verdict changes.

## Deciding experiment

1. Add failing parser tests for explicit theorem representation and malformed
   references.
2. Add failing semantic tests for tutorial 012, valid theorem use, theorem
   self-reference, and the absence of theorem bodies from delta authority.
3. Add `Declaration::Theorem` and resolve its identifiers exactly as for the
   supported declaration fragment.
4. Add a three-valued proposition judgment: infer the theorem type and compare
   its type with `Sort 0`; preserve `UNKNOWN` at unresolved conversion edges.
5. Check the proof under the old environment, then install only level
   parameters and declared type. Do not retain an executable body.
6. Replay all Rust/Python/ledger gates and the tutorial prefix through 014.
7. Retain only if all falsifiers survive; otherwise revert the mechanism and
   record the failed experiment.

## Qualification hardening

Keep the historical six-case G2 qualification unchanged. In the same
exact-head workflow, build the pinned Arena tutorial and replay ordered cases
001-011, recording fixture hashes, expected and actual exits, candidate SHA,
and Arena SHA in a distinct qualification document embedded in the run
attestation.

## Portable semantic layer

Create a small `IdealLean` Lean project with no dependency on Rust data
structures. It will state only the currently earned fragment, with explicit
scope limitations. Its first executable proofs cover:

- theorem installation extends a prior environment only after proposition and
  proof premises;
- an installed theorem has a signature but no reducible body;
- the theorem under installation is absent from its premise environment;
- opening a binder with the same semantic local preserves shared identity.

These theorems warrant the representation boundary; they do not yet prove the
Rust checker refines the specification.

## Promotion and next residual

If retained, the shallow runtime representative is a constant signature with
no theorem proof body. Preserve the input declaration and qualification record
as deep provenance. After exact cases 001-014 pass, run the next ordered Arena
tutorial case and freeze its first mismatch; do not select a feature from the
capability wish list.
