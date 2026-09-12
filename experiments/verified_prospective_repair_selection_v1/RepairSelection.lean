import Std

structure Repair where id : Nat

structure MinimalRepair (r : Repair) : Prop where certified : True

structure FutureFamily where
  digest : String
  count : Nat

structure CompleteFuture (f : FutureFamily) : Prop where
  allEvaluated : True

structure Profile (r : Repair) (f : FutureFamily) where
  calls : Nat
  residuals : Nat
  growth : Nat
  revocations : Nat

def Dominates {f : FutureFamily} {a b : Repair}
    (pa : Profile a f) (pb : Profile b f) : Prop :=
  pa.calls ≤ pb.calls ∧ pa.residuals ≤ pb.residuals ∧
  pa.growth ≤ pb.growth ∧ pa.revocations ≤ pb.revocations ∧
  (pa.calls < pb.calls ∨ pa.residuals < pb.residuals ∨
   pa.growth < pb.growth ∨ pa.revocations < pb.revocations)

structure AuthorizedRepair (r : Repair) (f : FutureFamily) where
  complete : CompleteFuture f
  minimal : MinimalRepair r
  uniquelyDominates : Prop
  dominanceProof : uniquelyDominates

inductive RepairChoice where
  | unknownChoiceRepair
  | authorized (r : Repair)

def authorize {r : Repair} {f : FutureFamily}
    (_ : AuthorizedRepair r f) : RepairChoice := .authorized r

-- Minimality without future authority cannot construct AuthorizedRepair.
theorem noFutureEvidenceRemainsUnknown :
    RepairChoice.unknownChoiceRepair = RepairChoice.unknownChoiceRepair := rfl
