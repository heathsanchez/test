"""Independent exact-invocation lineage control; fixture qualification only.

This separately frozen control targets a reviewer-discovered causal omission:
an instrument and an individual source-bound execution witness are different
ancestors.  Registering the witness in a JSON descriptor is not a Metatron edge.
"""
from __future__ import annotations

import copy
import json

import pytest

from .native_v43_test_support import implementation, modern_environment, project_factory
from .test_native_materialization_v43 import (
    closure_agrees, native_runtime, no_effect_launches, node, stack,
)


def test_exact_source_invocation_witness_recloses_native_capability_and_outcome(
        project_factory, tmp_path):
    module, machine, materializer = stack(tmp_path)
    worker = implementation('native_execution_v43')
    alpha = project_factory('alpha')
    beta = project_factory('beta')
    unrelated_case = project_factory('unrelated', generated=False)
    alpha_request = module.request(alpha.contract, alpha.authority, alpha.policy)
    beta_request = module.request(beta.contract, beta.authority, beta.policy)
    materializer.register('source-alpha', alpha_request)
    materializer.register('source-beta', beta_request)
    instrument = materializer.admit(alpha_request)
    _, alpha_witness = materializer.execute(instrument, alpha_request)
    beta_evidence, beta_witness = materializer.execute(instrument, beta_request)

    certificate = worker.collect(beta.with_evidence(beta_evidence), beta.authority,
        tmp_path / 'beta-collection', policy=beta.policy)
    dependent = native_runtime(machine, beta, certificate, tmp_path / 'beta-native',
        evidence=beta_evidence, instrument=instrument)
    native_capability = dependent.admit({'replacements': []})
    native_receipt, native_outcome = dependent.execute(native_capability)
    assert native_receipt['status'] == 'PASS_NATIVE'
    assert native_receipt['junit']['passed'] == 2
    binding = machine.get(machine.descriptor(native_capability).source['materialization_binding'])
    assert binding['consequence_id'] == beta_witness
    original_binding = copy.deepcopy(dependent.materialization_binding)
    dependent.materialization_binding['consequence_id'] = alpha_witness
    try:
        with no_effect_launches():
            with pytest.raises((ValueError, PermissionError)):
                dependent.execute(native_capability)
    finally:
        dependent.materialization_binding = original_binding

    unrelated_certificate = worker.collect(unrelated_case.contract, unrelated_case.authority,
        tmp_path / 'unrelated-collection', policy=unrelated_case.policy)
    unrelated = native_runtime(machine, unrelated_case, unrelated_certificate,
                               tmp_path / 'unrelated-native')
    unrelated_capability = unrelated.admit({'replacements': []})
    assert unrelated.execute(unrelated_capability)[0]['status'] == 'PASS_NATIVE'

    cap = machine.descriptor(native_capability)
    source_ident = dependent.source
    observation_ident = cap.dependencies[1]
    graph_before = {
        'native_descriptor_has_exact_witness': beta_witness in cap.dependencies,
        'native_node_has_exact_witness': beta_witness in node(machine, native_capability).premises,
        'native_observation_has_exact_witness': beta_witness in node(machine, observation_ident).premises,
    }
    # The original append/revoke/flush operation is used directly because this
    # witness is a verified consequence, not an executable Capability descriptor.
    revocation = machine.append('revoke', {'target': beta_witness,
        'reason': 'independent V43 exact source-B invocation withdrawal',
        'controlled_local_withdrawal': True, 'upstream_revocation': False})
    machine.flush()
    assert node(machine, revocation).payload['target'] == beta_witness
    closure_agrees(machine)
    live = set(machine.mt.live_ids(machine.log))
    affected = [observation_ident, native_capability, native_outcome]
    # Immutable source input identity remains as provenance.  Current warranted
    # observation/execution consequences require the actual invocation witness.
    unaffected = [source_ident, instrument, alpha_witness, unrelated_capability]
    graph_after = {
        'exact_witness_withdrawn': beta_witness not in live,
        'affected_are_withdrawn': all(ident not in live for ident in affected),
        'unrelated_and_other_source_survive': all(ident in live for ident in unaffected),
    }
    with no_effect_launches():
        with pytest.raises(PermissionError):
            dependent.execute(native_capability)
    assert unrelated.execute(unrelated_capability)[0]['status'] == 'PASS_NATIVE'
    closure_agrees(machine)
    record = {'schema': 'UDM_EXACT_MATERIALIZATION_INVOCATION_LINEAGE_CONTROL_V43',
        'instrument': instrument, 'source_alpha_witness': alpha_witness,
        'source_beta_witness': beta_witness, 'native_source': source_ident,
        'native_observation': observation_ident,
        'native_capability': native_capability, 'native_outcome': native_outcome,
        'unrelated_capability': unrelated_capability, 'graph_before': graph_before,
        'graph_after': graph_after, 'native_status': native_receipt['status'],
        'native_assertions': native_receipt['junit'],
        'other_source_binding_rejected_before_launch': True,
        'rejected_execution_started_no_effects': True}
    (tmp_path / 'INVOCATION_LINEAGE.json').write_text(json.dumps(record,sort_keys=True)+'\n')
    assert all(graph_before.values()), graph_before
    assert all(graph_after.values()), graph_after
