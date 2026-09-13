from dataclasses import dataclass
from enum import Enum, auto

class Decision(Enum):
    EXECUTE_SETTLED=auto()
    EXECUTE_REUSE=auto()
    UNKNOWN=auto()
    DEVELOP=auto()
    WAIT_FUTURE=auto()
    PROMOTE=auto()
    REJECT_CHANGE=auto()
    CONTRACT=auto()

@dataclass(frozen=True)
class Encounter:
    verified_witness: bool=False
    retained_capability_applicable: bool=False
    search_complete: bool=False
    certified_inadequate: bool=False
    minimal_verified_repairs: int=0
    future_unique_survivor: bool=False
    protected_replay_ok: bool=True
    redundancy_proven: bool=False

def resolve(e: Encounter) -> Decision:
    # Existing verified capability/witness has priority: do not reopen development.
    if e.verified_witness:
        return Decision.EXECUTE_SETTLED
    if e.retained_capability_applicable:
        return Decision.EXECUTE_REUSE

    # Contraction is licensed only by proved redundancy with replay intact.
    if e.redundancy_proven:
        return Decision.CONTRACT if e.protected_replay_ok else Decision.REJECT_CHANGE

    # A proposed repair that damages protected consequence is inadmissible.
    if e.minimal_verified_repairs > 0 and not e.protected_replay_ok:
        return Decision.REJECT_CHANGE

    # Failure without completeness/obstruction is not authority to grow.
    if not e.certified_inadequate:
        return Decision.UNKNOWN

    # Certified inadequacy licenses development, but not arbitrary choice.
    if e.minimal_verified_repairs == 0:
        return Decision.DEVELOP
    if e.minimal_verified_repairs > 1 and not e.future_unique_survivor:
        return Decision.WAIT_FUTURE
    if e.future_unique_survivor:
        return Decision.PROMOTE
    # One verified minimum with replay intact can be admitted/promoted.
    if e.minimal_verified_repairs == 1:
        return Decision.PROMOTE
    raise AssertionError("unreachable")
