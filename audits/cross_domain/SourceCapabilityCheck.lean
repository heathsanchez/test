import EulerBlowup.Elementary
import ABAngleBounds

/-! The actual source declaration is imported, not reconstructed from a
paper or a theorem name. The local capability is checked against its source
statement. Both are independently kernel-checked. -/
namespace CrossDomainResidual.SourceCapabilityCheck

theorem source_tilt_replay {ψ₀ G : ℝ} (hψ : 0 < ψ₀) (hG : 0 < G) :
    1 / G - ψ₀ ^ 2 / (3 * G ^ 3) ≤ Real.arctan (ψ₀ / G) / ψ₀ ∧
    Real.arctan (ψ₀ / G) / ψ₀ ≤ 1 / G :=
  EulerBlowup.tilt_from_stretch hψ hG

theorem extracted_tilt_replay {ψ₀ G : ℝ} (hψ : 0 < ψ₀) (hG : 0 < G) :
    1 / G - ψ₀ ^ 2 / (3 * G ^ 3) ≤ Real.arctan (ψ₀ / G) / ψ₀ ∧
    Real.arctan (ψ₀ / G) / ψ₀ ≤ 1 / G :=
  ABAngleBounds.tilt_from_stretch hψ hG

#print axioms source_tilt_replay
#print axioms extracted_tilt_replay
end CrossDomainResidual.SourceCapabilityCheck
