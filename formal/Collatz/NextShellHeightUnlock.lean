import Collatz.RetroactiveFutureQuotient

set_option maxRecDepth 16384

namespace CollatzFinal
namespace SourceProduct

/-!
V174 — A NEXT-DYADIC-SHELL TERMINAL-SEEDED REAL TWO-CLOCK JOIN.

The source n=13,774,695 remained UNSEEDED in the qualified finite
H=200 graph of original positive sources below 2^25 (a finite CLOCK
timeout, not a claim it is divergent).

A source p=61,407,743 that is admitted at the next cutoff 2^26
shares a genuine endpoint at clocks (207,57) and has an independently
checked terminal certificate at clock 201. Every individual witness
clock <=208=H(26), while the original n reaches terminal at its direct
first clock 351.

This is a source-height-only finite proof-reuse capability, not a
universal coverage theorem. Collatz globally UNKNOWN.
-/

/-- Exact observed endpoint pair with two independent true shortcut
clocks. The new positive original source lies in [2^25, 2^26). -/
def v174ShellActualEdge : V168TwoClockEdge where
  source := 13774695
  other := 61407743
  sourceClock := 207
  otherClock := 57
  sourcePositive := by omega
  otherPositive := by omega
  sameEndpoint := by decide

/-- Terminal-certified new original source, independently checked by
the true successor law, not by an earlier-source assertion. -/
def v174ShellTerminalSeed : V168TerminalSeed where
  source := 61407743
  clock := 201
  positive := by omega
  endpointTerminal := by
    have h : iter shortcut 201 61407743 = 2 := by decide
    rw [h]
    simp [Terminal]

/-- Genuine one-edge source-and-clock ledger reusing the verified
terminal seed at source p. -/
theorem v174ShellLedgerCloses :
    V168LedgerCloses
      [v174ShellActualEdge]
      [v174ShellTerminalSeed]
      13774695 := by
  refine ⟨v174ShellTerminalSeed, by simp, ?_⟩
  have he : v174ShellActualEdge ∈ [v174ShellActualEdge] := by simp
  exact V168Path.observed v174ShellActualEdge he

/-- Independently kernel-checked terminal consequence of the full
positive original source, without calling any global convergence fact. -/
theorem v174ShellTerminalConsequence :
    CollatzGood 13774695 := by
  exact v168_every_ledger_closure_is_genuine
    [v174ShellActualEdge]
    [v174ShellTerminalSeed]
    13774695
    v174ShellLedgerCloses

/-- Height is needed for THIS finite ledger but not for the original
source or a restricted shorter-clock witness. -/
theorem v174ShellOriginalHeightGuard :
    0 < 13774695 ∧ 13774695 < 2^25 ∧
    2^25 ≤ 61407743 ∧ 61407743 < 2^26 := by
  decide

theorem v174ShellAllIndividualClocksAtMost208 :
    v174ShellActualEdge.sourceClock ≤ 208 ∧
    v174ShellActualEdge.otherClock ≤ 208 ∧
    v174ShellTerminalSeed.clock ≤ 208 := by
  decide

/-- Arithmetic audit of the exact common positive endpoint; its type
is Nat and the original source IDs are not quotient aliases. -/
theorem v174ShellSharedEndpoint :
    iter shortcut 207 13774695 = 191866796 ∧
    iter shortcut 57 61407743 = 191866796 := by
  decide

#print axioms v174ShellLedgerCloses
#print axioms v174ShellTerminalConsequence
#print axioms v174ShellOriginalHeightGuard
#print axioms v174ShellAllIndividualClocksAtMost208
#print axioms v174ShellSharedEndpoint

end SourceProduct
end CollatzFinal
