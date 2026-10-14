"""Small consequential-evidence core. Exact rational arithmetic, stdlib only.

Source claims are input by an explicit HUMAN-AUTHORED semantic adapter. This is
not autonomous source-to-theory interpretation.
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

F = Fraction
C = F(299792458)

class UnknownEvidence(ValueError):
    pass

@dataclass(frozen=True)
class Quantity:
    kind: str
    value: Fraction
    sigma: Fraction
    unit: str
    source_event: str
    theory: str
    supports: tuple[str, ...]

    def __post_init__(self):
        if self.sigma <= 0:
            raise UnknownEvidence("INVALID_STANDARD_UNCERTAINTY")
        if len(set(self.supports)) != len(self.supports):
            raise UnknownEvidence("DUPLICATED_SUPPORT")

def q(kind: str, value: str, sigma: str, unit: str,
      event: str, theory: str, supports: Iterable[str]) -> Quantity:
    return Quantity(kind,F(value),F(sigma),unit,event,theory,tuple(supports))

def canonical(a: Quantity) -> Quantity:
    """Return a canonical dimensioned type, no implicit unit coercion."""
    if a.kind == "proton_radius" and a.unit == "fm":
        return a
    if a.kind == "rydberg_frequency" and a.unit == "kHz":
        return a
    if a.kind == "rydberg_constant" and a.unit == "m^-1":
        return Quantity("rydberg_frequency",a.value*C/1000,a.sigma*C/1000,
                        "kHz",a.source_event,a.theory,a.supports)
    if a.kind == "hydrogen_transition_frequency" and a.unit == "kHz":
        return a
    raise UnknownEvidence("UNSUPPORTED_DIMENSION_OR_UNIT")

def robust_consistency(a: Quantity,b: Quantity,threshold: Fraction=F(2)):
    """Prove |x-y| < threshold*sigma(x-y) for every rho in [-1,1].

    sigma_delta^2=sigma_a^2+sigma_b^2-2*rho*sigma_a*sigma_b.
    For all |rho|<=1, sigma_delta >= |sigma_a-sigma_b|.
    This sufficient (in fact for two nonzero unequal sigmas necessary)
    conservative criterion never assumes cross-study independence.
    """
    a,b=canonical(a),canonical(b)
    if a.kind != b.kind or a.unit != b.unit:
        raise UnknownEvidence("INCOMPATIBLE_MEASURANDS")
    if a.source_event == b.source_event:
        raise UnknownEvidence("SAME_EVIDENCE_EVENT_NOT_INDEPENDENT_CONTRAST")
    delta=abs(a.value-b.value)
    min_sigma=abs(a.sigma-b.sigma)
    result={"quantity":a.kind,"unit":a.unit,
            "delta_exact":str(delta),"minimum_difference_sigma_exact":str(min_sigma),
            "cross_study_covariance":"UNKNOWN",
            "formal_bound":"forall rho in [-1,1], sigma_delta >= abs(sigma_a-sigma_b)",
            "two_event_contrast":True}
    if delta < threshold*min_sigma:
        result["verdict"]="WARRANTED_BOUNDED_ROBUST_CONSISTENCY"
        result["maximum_possible_z"]=str(delta/min_sigma)
    else:
        result["verdict"]="UNKNOWN_CORRELATION_COULD_CHANGE_THRESHOLD_DECISION"
        result["maximum_possible_z"]="UNBOUNDED" if min_sigma==0 else str(delta/min_sigma)
    return result

def joint_covariance_diagnostic(rho: Fraction):
    """Normalized outputs: diagnostic only, NOT an invented physical measurand."""
    if abs(rho)>1:
        raise UnknownEvidence("NON_POSITIVE_SEMIDEFINITE_COVARIANCE")
    return {"correlation":str(rho),
            "correlated_sum_variance":str(2+2*rho),
            "naive_independence_variance":str(F(2)),
            "covariance_matrix_determinant":str(1-rho*rho)}

class Ledger:
    def __init__(self):
        self.events={}
        self.products={}
        self.revoked_supports=set()

    def add_event(self,event_id: str,source_digest: str,source_url: str):
        if not source_digest or len(source_digest)!=64 or not source_url.startswith("https://"):
            raise UnknownEvidence("INVALID_SOURCE_IDENTITY")
        incoming=(source_digest,source_url)
        old=self.events.get(event_id)
        if old is not None and old!=incoming:
            raise UnknownEvidence("CONFLICTING_SOURCE_ID")
        self.events[event_id]=incoming
        return old is None

    def add_product(self,pid: str,quantity: Quantity):
        if quantity.source_event not in self.events:
            raise UnknownEvidence("UNQUALIFIED_SOURCE_EVENT")
        old=self.products.get(pid)
        if old is not None and old!=quantity:
            raise UnknownEvidence("CONFLICTING_PRODUCT_ID")
        self.products[pid]=quantity
        return old is None

    def resolve(self,pid):
        x=self.products.get(pid)
        if x is None:
            return "UNKNOWN_PRODUCT"
        if any(s in self.revoked_supports for s in x.supports):
            return "UNKNOWN_REVOKED_SUPPORT"
        return "WARRANTED_BOUNDED_DECLARED_SOURCE_PRODUCT"

    def revoke(self,support):
        self.revoked_supports.add(support)

    def restore(self,support):
        self.revoked_supports.discard(support)

    def count_events(self):
        return len(self.events)

    def source_fingerprint_set(self):
        return frozenset(d[0] for d in self.events.values())

    def insert_claim(self,source_event: str,claimed_kind: str,role: str):
        # A paper's use of alpha as a fixed INPUT is not an alpha observation.
        if claimed_kind=="inverse_alpha" and role!="MEASURED_ALPHA":
            raise UnknownEvidence("INPUT_NOT_INDEPENDENT_ALPHA_OBSERVATION")
        if source_event not in self.events:
            raise UnknownEvidence("UNQUALIFIED_SOURCE_EVENT")
        return True

def contrast_measured_predicted(x:Quantity,pred:Quantity):
    x,pred=canonical(x),canonical(pred)
    if x.kind!="hydrogen_transition_frequency" or pred.kind!=x.kind:
        raise UnknownEvidence("INCOMPATIBLE_MEASURANDS")
    # Here paper reports 0.00(53), and quadrature is an attributed paper
    # interpretation. Does not independently verify shared theory inputs.
    return {"difference_kHz":str(x.value-pred.value),
            "variance_kHz_sq":str(x.sigma*x.sigma+pred.sigma*pred.sigma),
            "attribution":"REPORTED_MODEL_DEPENDENT_CONTRAST",
            "independent_QED_validation":False}
