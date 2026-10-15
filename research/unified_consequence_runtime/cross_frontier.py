"""Receipt-bound native route readiness through the original FLASH closure.

Metatron remains the only persisted warrant authority. This module projects its
records into an original ``FlashClosure`` over separately registered active
frontiers. Its finite semantics mean *an admitted executable route is ready for
an exact declared profile*, not that a receipt table is the native program.
Actual effects and fresh verification remain in the source-native adapters.

The public Python API is not a non-bypassable hostile-process reference monitor.
"""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import time

from .developmental_machine import canonical, check_source, digest


CONTRACT_FIELDS = frozenset(("input_type", "output_type", "authority_snapshot", "verifier_id"))
REGISTRATION = "native_frontier_registration"
PUBLICATION = "native_frontier_route"
AVAILABLE = "INDEPENDENTLY_WARRANTED_EXECUTABLE_ROUTE_AVAILABLE"
PREFIX = "udm:warrant:"
ROUTE_PREFIX = "udm:native-frontier-route:"
VERIFICATION_KINDS = frozenset(("native_observation_verification", "native_constructor_verification"))


def _contract(value):
    if not isinstance(value, dict) or set(value) != CONTRACT_FIELDS:
        raise ValueError("frontier contract requires exact typed authority and verifier fields")
    if any(not isinstance(item, str) or not item for item in value.values()):
        raise ValueError("frontier contract fields must be nonempty strings")
    return dict(value)


def _profiles(values):
    if (not isinstance(values, (list, tuple)) or not values or
            any(not isinstance(value, str) or not value for value in values) or
            len(set(values)) != len(values)):
        raise ValueError("native frontier profiles must be unique nonempty strings")
    return sorted(values)


def _nodes(machine):
    return {node.id: node for node in machine.log}


def _validator_source(verification_kind):
    """The two installed native adapters, rather than a caller-chosen checker."""
    if verification_kind == "native_observation_verification":
        return Path(__file__).with_name("native_observation.py")
    if verification_kind == "native_constructor_verification":
        return Path(__file__).with_name("native_constructor.py")
    raise ValueError("unsupported native frontier verification boundary")


def _native(machine):
    check_source(machine.components / "flash", "flash")
    module = importlib.import_module("realitygraph.flash")
    expected = machine.components / "flash" / "realitygraph" / "flash.py"
    if Path(module.__file__).resolve() != expected.resolve():
        raise ValueError("frontier closure imported from different source")
    capability = importlib.import_module("realitygraph.capability").FiniteCapability
    return module, capability


def register_frontier(machine, frontier_id, *, contract, profile, request):
    """Declare a protected native profile before any resolving route is admitted.

    The request is retained byte-exactly as content-addressed input. Registration
    is independent of any candidate capability so withdrawal reopens the frontier
    instead of deleting the obligation itself.
    """
    if not isinstance(frontier_id, str) or not frontier_id:
        raise ValueError("native frontier requires a stable identifier")
    contract = _contract(contract)
    _profiles([profile])
    if not isinstance(request, dict):
        raise ValueError("native frontier requires a typed request object")
    payload = {"schema": "metalogic.native-frontier.registration.v1",
               "frontier_id": frontier_id, "contract": contract, "profile": profile,
               "request": machine.put(request),
               "meaning": "exact receipt-bound native route readiness; native execution still required"}
    previous = [node for node in machine.log
                if node.kind == REGISTRATION and node.payload.get("frontier_id") == frontier_id]
    if previous:
        if len(previous) != 1 or previous[0].payload != payload:
            raise ValueError("native frontier identity conflict")
        return previous[0].id
    node_id = machine.append(REGISTRATION, payload)
    machine.flush()
    return node_id


def _publication_binding(machine, payload, premises):
    nodes = _nodes(machine)
    contract = _contract(payload["contract"])
    profiles = _profiles(payload["profiles"])
    cap_id, evidence_id = payload["capability_id"], payload["verification_id"]
    cap_node, verified = nodes[cap_id], nodes[evidence_id]
    if cap_node.kind != "executable_capability":
        raise ValueError("native frontier route must retain an actual executable capability")
    cap = machine.descriptor(cap_id)
    if contract != _contract(cap.scope.get("frontier_contract")):
        raise ValueError("native frontier contract is outside independently verified capability scope")
    if not set(profiles) <= set(_profiles(cap.scope.get("frontier_profiles"))):
        raise ValueError("native frontier profile is outside independently verified capability scope")
    if verified.kind not in VERIFICATION_KINDS or evidence_id not in cap.evidence:
        raise ValueError("native frontier route lacks the capability's independent native evidence")
    if tuple(premises) != (cap_id, evidence_id):
        raise ValueError("native frontier publication has incorrect causal dependencies")
    if (verified.payload.get("program") != cap.program or
            payload.get("program") != cap.program or
            payload.get("receipt") != verified.payload.get("receipt") or
            payload.get("evidence_binding") != digest(canonical(verified.payload).encode()) or
            payload.get("source_sha256") != digest(canonical(cap.source).encode())):
        raise ValueError("native frontier publication does not bind actual source, program and evidence")
    if payload.get("meaning") != AVAILABLE or payload.get("schema") != "metalogic.native-frontier.route.v1":
        raise ValueError("wrong native frontier projection meaning")
    validator_sha = payload.get("validator_source_sha256", "")
    if (not isinstance(validator_sha, str) or len(validator_sha) != 64 or
            any(c not in "0123456789abcdef" for c in validator_sha)):
        raise ValueError("native frontier route lacks a source-bound admission validator")
    if digest(_validator_source(verified.kind).read_bytes()) != validator_sha:
        raise ValueError("native frontier admission validator source changed after publication")
    # Content-addressed reads reject tampered code/data/evidence. The original
    # domain adapter checked receipt semantics before publication; FLASH checks
    # exact readiness facts and causal liveness, not arbitrary domain science.
    machine.get(cap.program)
    machine.get(cap.observation)
    receipt = machine.get(payload["receipt"])
    if not isinstance(receipt, dict) or not receipt:
        raise ValueError("native frontier route has no retained native receipt")
    return cap, contract, profiles


def publish_frontier_route(machine, capability_id, *, contract, profiles,
                           verification_id, validate, evidence_binding=None):
    """Publish exact profile readiness after original domain-native validation.

    ``validate`` must be the same machine's domain adapter validator. Acquisition
    and verification remain separate: an executable descriptor alone cannot
    produce this publication. This is a local scientific admission API, not a
    signature or security boundary against code with access to public append.
    """
    contract, profiles = _contract(contract), _profiles(profiles)
    owner = getattr(validate, "__self__", None)
    if not callable(validate) or getattr(owner, "machine", None) is not machine:
        raise ValueError("frontier publication requires this machine's native adapter validator")
    if validate(capability_id) is False:
        raise ValueError("independent native adapter rejected frontier publication")
    nodes = _nodes(machine)
    live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    if capability_id not in live or verification_id not in live:
        raise PermissionError("native frontier publication support is withdrawn")
    cap = machine.descriptor(capability_id)
    verified = nodes[verification_id]
    expected_binding = digest(canonical(verified.payload).encode())
    if evidence_binding is not None and evidence_binding != expected_binding:
        raise ValueError("native frontier evidence binding differs from independent verification")
    source_file = inspect.getsourcefile(validate)
    if source_file is None:
        raise ValueError("native frontier validator source is unavailable")
    if Path(source_file).resolve() != _validator_source(verified.kind).resolve():
        raise ValueError("native frontier validator is outside the installed typed native adapter")
    payload = {"schema": "metalogic.native-frontier.route.v1",
               "capability_id": capability_id, "verification_id": verification_id,
               "program": cap.program, "receipt": verified.payload.get("receipt"),
               "evidence_binding": expected_binding,
               "source_sha256": digest(canonical(cap.source).encode()),
               "validator_source_sha256": digest(Path(source_file).read_bytes()),
               "contract": contract, "profiles": profiles, "meaning": AVAILABLE}
    _publication_binding(machine, payload, (capability_id, verification_id))
    node_id = machine.append(PUBLICATION, payload, (capability_id, verification_id))
    machine.flush()
    return node_id


def reclose_frontiers(machine):
    """Recompute every registered frontier using original FLASH, never new state.

    The JSON output is a reproducible derived cache bound to the exact log hash.
    Startup and execution rebuild it; editing this cache cannot grant a route.
    """
    started = time.perf_counter()
    registrations = [node for node in machine.log if node.kind == REGISTRATION]
    if not registrations:
        return {"schema": "metalogic.native-frontier.closure.v1", "frontiers": {},
                "changed_frontiers": [], "flash_radius": 0}
    flash, FiniteCapability = _native(machine)
    live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    obligations = []
    request_nodes = {}
    for node in registrations:
        payload = node.payload
        frontier_id = payload["frontier_id"]
        if frontier_id in request_nodes:
            raise ValueError("duplicate native frontier identifier")
        contract = _contract(payload["contract"])
        profile = _profiles([payload["profile"]])[0]
        machine.get(payload["request"])
        request_nodes[frontier_id] = node
        obligations.append(flash.LiveObligation(
            obligation_id=frontier_id, input_type=contract["input_type"],
            source_input_type=contract["input_type"], output_type=contract["output_type"],
            oracle=((profile, AVAILABLE),), transport_to_source=((profile, profile),),
            contract=flash.FlashContract(contract["authority_snapshot"], contract["verifier_id"]),
            domain="source-native-protected-frontier"))
    closure = flash.FlashClosure(obligations, kernel="udm-original-flash-native-frontiers-v1")
    runtime = flash.FlashEventRuntime(closure)
    publications = {}
    # Preserve every original causal record, including revoked history. The
    # projection uses the same conjunction of premises as canonical Metatron.
    for node in machine.log:
        if node.kind == "revoke":
            runtime.apply(flash.CapabilityRevocationEvent(
                "frontier-support-revoke:" + node.id,
                PREFIX + node.payload["target"], node.payload["reason"]))
            continue
        rows = ((node.id, digest(canonical(node.record()).encode())),)
        support = tuple(PREFIX + parent for parent in node.premises)
        cap = FiniteCapability(PREFIX + node.id, "SupportNodeId", "SupportRecordSHA256",
                               rows, (node.id,), node.id, support,
                               "udm-local-warrant-log-v1", "metatron-causal-support-projection-v1",
                               (node.id,), 0)
        runtime.apply(flash.CapabilityAdmissionEvent(
            "frontier-support:" + node.id, cap, rows, support, "support-projection-only"))
        if node.kind != PUBLICATION:
            continue
        _cap, contract, profiles = _publication_binding(machine, node.payload, node.premises)
        rows = tuple((profile, AVAILABLE) for profile in profiles)
        projected_id = ROUTE_PREFIX + node.id
        route = FiniteCapability(projected_id, contract["input_type"], contract["output_type"],
                                 rows, tuple(profiles), node.payload["verification_id"], (),
                                 contract["authority_snapshot"], contract["verifier_id"],
                                 (node.id, node.payload["capability_id"]), 0)
        runtime.apply(flash.CapabilityAdmissionEvent(
            "frontier-route:" + node.id, route, rows, (PREFIX + node.id,),
            "independently-admitted-native-route-readiness-projection"))
        publications[projected_id] = node
    active = set(closure.active_capability_ids())
    if {item[len(PREFIX):] for item in active if item.startswith(PREFIX)} != set(machine.mt.live_ids(machine.log)):
        raise AssertionError("native frontier FLASH disagrees with canonical support liveness")
    previous = getattr(machine, "frontiers", {}).get("frontiers", {})
    frontiers = {}
    for frontier_id, obligation in closure.obligations.items():
        request = request_nodes[frontier_id]
        candidates = [projected for projected in sorted(publications)
                      if projected in active and closure._capability_solves(
                          closure.capabilities[projected].capability, obligation)]
        capability_ids = sorted({publications[item].payload["capability_id"] for item in candidates})
        if request.id not in live:
            status, capability_ids = "UNKNOWN_MISSING_AUTHORITY", []
        else:
            status = "READY" if len(capability_ids) == 1 else "UNKNOWN_CHOICE" if capability_ids else "UNKNOWN_SEARCH"
        frontiers[frontier_id] = {
            "status": status, "capability_id": capability_ids[0] if status == "READY" else None,
            "candidates": capability_ids, "publication_ids": [publications[item].id for item in candidates],
            "registration_id": request.id, "request": request.payload["request"],
            "profile": request.payload["profile"], "contract": request.payload["contract"],
            "flash_status": obligation.status, "native_execution": "REQUIRED_ON_ACTIVATION",
            "expressivity": "UNKNOWN", "external_authority": "UNCHANGED"}
    changed = sorted(frontier_id for frontier_id in set(previous) | set(frontiers)
                     if previous.get(frontier_id) != frontiers.get(frontier_id))
    result = {"schema": "metalogic.native-frontier.closure.v1",
              "ledger_sha256": digest(machine.mt.dumps(machine.log).encode()),
              "frontiers": frontiers, "changed_frontiers": changed, "flash_radius": len(changed),
              "original_flash_events": closure.flash_events,
              "meaning": "receipt-bound readiness only; original native execution remains independent",
              "external_reference_monitor": "UNKNOWN_NONBYPASSABILITY"}
    (machine.state / "native-frontiers.json").write_text(canonical(result))
    machine.costs.append({"phase": "cross_frontier_original_flash_reclosure",
                          "seconds": time.perf_counter() - started,
                          "active_frontiers": len(frontiers), "changed_frontiers": len(changed)})
    return result


def require_frontier_route(machine, frontier_id, *, validate=None):
    """Return a live unique native route, preserving choice/search UNKNOWNs."""
    machine.frontiers = reclose_frontiers(machine)
    if frontier_id not in machine.frontiers["frontiers"]:
        raise KeyError("native frontier was not registered")
    result = dict(machine.frontiers["frontiers"][frontier_id])
    if result["status"] == "READY" and validate is not None:
        if validate(result["capability_id"]) is False:
            raise ValueError("independent native adapter rejected retained frontier route")
        # Adapter checks can observe revocation or append evidence. Never return
        # a stale route following a validation that changed canonical state.
        machine.frontiers = reclose_frontiers(machine)
        current = machine.frontiers["frontiers"][frontier_id]
        if current["status"] != "READY" or current["capability_id"] != result["capability_id"]:
            raise PermissionError("native frontier route changed during validation")
    return result
