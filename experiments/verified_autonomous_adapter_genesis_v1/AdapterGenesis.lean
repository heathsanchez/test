import TypedResidualKernel
namespace AdapterGenesis
inductive Role where | scan | filter | first | pair | extend | temporal deriving DecidableEq
inductive Token where | zx9 | qa2 | mn7 | rv4 | kp1 | ht8 deriving DecidableEq
def Encoding := Role → Token
def compiled (φ : Encoding) : List Role → List Token := List.map φ
structure AdapterCertificate (φ : Encoding) : Prop where
  injective : Function.Injective φ
theorem certified_compilation (φ : Encoding) (p : AdapterCertificate φ) (a b : Role) :
    φ a = φ b → a = b := by
  intro h
  exact p.injective h
def fixedEncoding : Encoding | .scan=>.zx9 | .filter=>.qa2 | .first=>.mn7 | .pair=>.rv4 | .extend=>.kp1 | .temporal=>.ht8
theorem fixedEncoding_certified : AdapterCertificate fixedEncoding := by constructor; intro a b h; cases a <;> cases b <;> simp_all [fixedEncoding]
end AdapterGenesis
