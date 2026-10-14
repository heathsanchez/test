"""Exact provenance-preserving conservative uncertainty envelope.

This is ordinary arithmetic, NOT a new physical result, source parser or Lean proof.
A single report's error components may be arbitrarily correlated, and separate
reports may be arbitrarily correlated. Printed digits may be rounded by half a
last displayed unit. No duplicate observations follow from model reanalyses.
"""
from dataclasses import dataclass
from fractions import Fraction as F

class Unknown(ValueError):
    pass

@dataclass(frozen=True)
class UncertainComponent:
    name: str
    sigma: F
    displayed_quantum: F
    def __post_init__(self):
        if self.sigma<0 or self.displayed_quantum<=0:
            raise Unknown("INVALID_UNCERTAINTY_COMPONENT")
    @property
    def upper_sigma(self):
        return self.sigma + self.displayed_quantum / 2

@dataclass(frozen=True)
class ReportedEstimate:
    claim_id: str
    kind: str
    unit: str
    center: F
    center_displayed_quantum: F
    components: tuple[UncertainComponent,...]
    original_data_roots: tuple[str,...]
    source_id: str
    method_id: str
    def __post_init__(self):
        if self.center_displayed_quantum<=0:
            raise Unknown("MISSING_PRECISION_METADATA")
        if not self.components:
            raise Unknown("MISSING_UNCERTAINTY")
        if len(set(self.original_data_roots))!=len(self.original_data_roots):
            raise Unknown("DUPLICATE_ORIGINAL_ROOTS")
    @property
    def center_interval(self):
        return (self.center-self.center_displayed_quantum/2,
                self.center+self.center_displayed_quantum/2)
    @property
    def sigma_upper(self):
        return sum((c.upper_sigma for c in self.components),F(0))

def e(claim_id,kind,center,center_quantum,comp_specs,roots,source,method,unit="fm"):
    return ReportedEstimate(claim_id,kind,unit,F(center),F(center_quantum),
      tuple(UncertainComponent(name,F(std),F(quantum))
            for name,std,quantum in comp_specs),
      tuple(roots),source,method)

def rounded_covariance_envelope(a:ReportedEstimate,b:ReportedEstimate,threshold=F(2)):
    """Strict sufficient guarantee valid for any allowed statistical covariance.

    Triangle/Cauchy: SD(diff) <= SD(a)+SD(b) <= sum(all upper components).
    For published central-value rounding intervals, |diff| >= interval gap.
    If gap > k * SD_upper, discrepancy necessarily exceeds k sigmas.
    Failure yields UNKNOWN: there might still be discrepancy.
    """
    if a.kind != b.kind:
        raise Unknown("MEASURAND_MISMATCH")
    if a.unit!=b.unit:
        raise Unknown("UNIT_MISMATCH_NO_SILENT_CONVERSION")
    if a.source_id==b.source_id or set(a.original_data_roots)&set(b.original_data_roots):
        raise Unknown("SAME_UNDERLYING_DATA_NO_INDEPENDENT_CONTRAST")
    a0,a1=a.center_interval;b0,b1=b.center_interval
    minimum_gap=max(F(0),a0-b1,b0-a1)
    u=a.sigma_upper+b.sigma_upper
    if u<=0: raise Unknown("INVALID_TOTAL_UNCERTAINTY")
    z=minimum_gap/u
    return {
      "verdict": ("WARRANTED_BOUNDED_ROUNDING_COVARIANCE_ROBUST_2SIGMA_TENSION"
          if z>threshold else "UNKNOWN_UNDER_ROUNDING_OR_COVARIANCE"),
      "comparison": [a.claim_id,b.claim_id],
      "conditional_on_same_physical_definition": True,
      "stat_sys_covariance": "UNKNOWN",
      "cross_study_covariance": "UNKNOWN",
      "threshold":str(threshold),
      "gap_lower_fm_exact":str(minimum_gap),
      "difference_sigma_upper_fm_exact":str(u),
      "guaranteed_z_lower":str(z),
      "independent_source_measurement_claim":False
    }

def nature():
    return e("nature_2026_rp","proton_electric_charge_radius",
      ".8406",".0001",[("reported_total",".0015",".0001")],
      ["nature2026:2s6p_raw_data"],"nature2026","atomic_2s6p")

def qattan_first():
    return e("qattan2026_electric_independent_fit","proton_electric_charge_radius",
      ".854",".001",[("stat",".002",".001"),("sys",".003",".001")],
      ["qattan_arrington2012_scattering","qattan_arrington_alsaad2015_scattering"],
      "qattan2026","independent_form_factor_fits")

def qattan_second():
    return e("qattan2026_electric_coupled_fit","proton_electric_charge_radius",
      ".851",".001",[("stat",".001",".001"),("sys",".001",".001")],
      ["qattan_arrington2012_scattering","qattan_arrington_alsaad2015_scattering"],
      "qattan2026","coupled_charge_magnetic_fit")

def qattan_magnetic():
    return e("qattan2026_magnetic_coupled_fit","proton_magnetic_radius",
      ".834",".001",[("stat",".002",".001"),("sys",".003",".001")],
      ["qattan_arrington2012_scattering","qattan_arrington_alsaad2015_scattering"],
      "qattan2026","coupled_charge_magnetic_fit")

def unsafe_midpoint_only(a,b):
    """Known defective baseline: ignores printed rounding and shared support."""
    return abs(a.center-b.center)/sum((c.sigma for c in a.components+b.components),F(0))

def independent_decimal_check(a,b):
    """Separate high-precision decimal-language baseline, not a second experiment."""
    from decimal import Decimal as D,getcontext
    getcontext().prec=55
    dec=lambda f:D(f.numerator)/D(f.denominator)
    a0,a1=a.center_interval;b0,b1=b.center_interval
    gap=max(D(0),dec(a0)-dec(b1),dec(b0)-dec(a1))
    sd=sum((dec(c.sigma)+dec(c.displayed_quantum)/2
             for c in a.components+b.components),D(0))
    return gap/sd
