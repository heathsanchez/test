import TypedResidualKernel
namespace CommonInvariant
inductive S where | a | b | c | d deriving DecidableEq
inductive T where | p | q | r | s | t deriving DecidableEq
inductive Pi where | zero | one deriving DecidableEq
def qs : S → Pi | .a=>.zero | .b=>.one | .c=>.zero | .d=>.one
def qt : T → Pi | .p=>.zero | .q=>.one | .r=>.one | .s=>.zero | .t=>.one
theorem carrier_sizes_differ : (4 : Nat) ≠ 5 := by decide
theorem source_surjective : Function.Surjective qs := by intro x; cases x <;> first | exact ⟨.a,rfl⟩ | exact ⟨.b,rfl⟩
theorem target_surjective : Function.Surjective qt := by intro x; cases x <;> first | exact ⟨.p,rfl⟩ | exact ⟨.q,rfl⟩
end CommonInvariant
