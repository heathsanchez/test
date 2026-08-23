from dataclasses import dataclass

@dataclass(frozen=True)
class ResearchState:
    name: str
    apparatus_valid: bool = True
    residual_sharp: bool = True
    existing_structure_unknown: bool = False
    repeated_local_failures: int = 0
    conditional_regimes: bool = False
    competing_explanations: int = 1
    deciding_test_ready: bool = False
    transfer_candidate_ready: bool = False
    retention_candidate_ready: bool = False
    external_import_active: bool = False

LIFECYCLE = {"REPAIR", "DISCOVER", "VERIFY", "TRANSFER", "RETAIN"}
MODES = {"EXPLOIT", "INSPECT", "MAP", "REFRAME", "DISCRIMINATE"}

def choose_lifecycle(s: ResearchState) -> str:
    # Lifecycle answers: what stage of research are we in?
    if not s.apparatus_valid:
        return "REPAIR"
    if s.retention_candidate_ready:
        return "RETAIN"
    if s.transfer_candidate_ready:
        return "TRANSFER"
    if s.deciding_test_ready and s.competing_explanations >= 2:
        return "VERIFY"
    return "DISCOVER"

def choose_mode(s: ResearchState) -> str:
    # Mode answers: how should we reason at this stage?
    if s.existing_structure_unknown:
        return "INSPECT"
    # IMPORT is an input channel, not a lifecycle state. It earns a reframe only
    # when local evidence already warrants changing altitude.
    if s.external_import_active and (s.repeated_local_failures >= 2 or not s.residual_sharp):
        return "REFRAME"
    if not s.residual_sharp:
        return "MAP"
    if s.deciding_test_ready and s.competing_explanations >= 2:
        return "DISCRIMINATE"
    if s.repeated_local_failures >= 2 or s.conditional_regimes:
        return "REFRAME"
    return "EXPLOIT"

def controller(s: ResearchState):
    return choose_lifecycle(s), choose_mode(s)

def local_only(s: ResearchState):
    # Strong local comparator: repairs invalid apparatus and can run an already-
    # prepared separator, but otherwise stays in the current frame and does not
    # initiate mapping, inspection, reframing, transfer, or retention.
    lifecycle = "REPAIR" if not s.apparatus_valid else ("VERIFY" if s.deciding_test_ready else "DISCOVER")
    mode = "DISCRIMINATE" if s.deciding_test_ready and s.competing_explanations >= 2 else "EXPLOIT"
    return lifecycle, mode
