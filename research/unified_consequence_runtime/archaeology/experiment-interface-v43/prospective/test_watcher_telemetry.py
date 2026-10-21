"""Data-only event/meter telemetry controls; no model or native calls."""
import copy
import importlib.util
from pathlib import Path

import pytest


def classify(events=(), before=None, after=None, process_started=True):
    path=Path(__file__).with_name('watch_actual_agent.py')
    spec=importlib.util.spec_from_file_location('_watcher_telemetry_control',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert hasattr(module,'_execution_telemetry'), 'separate watcher telemetry is absent'
    return module._execution_telemetry(events,before,after,process_started)


def meter():
    return {'arm_sha256':'a'*64,'started_at_unix':100,'native_calls':4,'attempts':[]}


def model():
    return {'type':'turn.completed','usage':{'input_tokens':2,'output_tokens':1}}


@pytest.mark.parametrize('events,started',[((),False),([{'type':'error','message':'launch refused'}],True),
    ([{'type':'turn.started'}],True)])
def test_unserved_launch_never_counts_as_agent_or_native_execution(events,started):
    value=classify(events,meter(),meter(),started)
    assert value['process_started'] is started
    assert value['model_turn_observed'] is False
    assert value['native_candidate_execution'] is False
    assert value['actual_agent_executed'] is False


@pytest.mark.parametrize('event',[model(),{'type':'item.completed','item':{'type':'agent_message','text':'proposal rationale'}}])
def test_observed_model_without_native_candidate_is_not_an_executed_comparator(event):
    value=classify([event],meter(),meter())
    assert value['model_turn_observed'] is True
    assert value['native_candidate_execution'] is False
    assert value['actual_agent_executed'] is False


def test_only_new_meter_attempt_with_positive_native_launch_counts_as_candidate_execution():
    before=meter();after=copy.deepcopy(before)
    after['native_calls']+=1;after['attempts'].append({'controller_attempts':{'native_calls':1}})
    value=classify([model()],before,after)
    assert value['new_native_attempt_calls']==1
    assert value['native_candidate_execution'] is True
    assert value['actual_agent_executed'] is True


@pytest.mark.parametrize('bad',[True,-1,0])
def test_boolean_negative_or_zero_calls_do_not_count_as_native_launch(bad):
    before=meter();after=copy.deepcopy(before)
    after['attempts'].append({'controller_attempts':{'native_calls':bad}})
    value=classify([model()],before,after)
    assert value['native_candidate_execution'] is False


def test_reset_changed_binding_or_missing_initial_meter_is_unknown():
    before=meter();before['attempts']=[{'controller_attempts':{'native_calls':1}}]
    after=meter();after['attempts']=[{'controller_attempts':{'native_calls':2}}]
    assert classify([model()],before,after)['native_candidate_execution'] is False
    after['arm_sha256']='b'*64
    assert classify([model()],meter(),after)['native_candidate_execution'] is False
    assert classify([model()],None,after)['native_candidate_execution'] is False
