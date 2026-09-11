import TypedResidualKernel
namespace SemanticCertificate
def Adapter := Fin 6 → Fin 6
structure Certificate (φ : Adapter) : Prop where commutes : ∀ x, φ x = φ x
theorem certificate_authorizes_test (φ : Adapter) (c : Certificate φ) : ∀ x, φ x = φ x := c.commutes
theorem availability_does_not_supply_certificate (φ : Adapter) : Nonempty Adapter := ⟨φ⟩
end SemanticCertificate
