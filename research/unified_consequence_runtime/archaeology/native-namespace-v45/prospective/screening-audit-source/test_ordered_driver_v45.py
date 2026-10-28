"""Source-free controls for exact original ordered process transport."""
import ast
import importlib.util
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent


def module():
    path=HERE/'ordered_screening_v45.py'
    assert path.is_file(), 'versioned original ordered transport missing'
    spec=importlib.util.spec_from_file_location('v45_ordered_driver',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_controller_preparation_never_executes_target_transport():
    source=module().prepare_driver_source()
    assert 'research.unified_consequence_runtime.qualify_native_frontier_v45' in source
    assert "os.environ['UDM_SCREENING_SOURCE_COMMIT']" in source
    assert "os.environ['UDM_SCREENING_AUTHORITY_SHA256']" in source
    assert "os.environ['UDM_PREQUERY_COMMIT']" in source
    assert 'UDM_V44_SCREENING' not in source
    assert 'source_snapshot' in source and 'SCREENING_ACTOR_ATTESTATION.json' in source


@pytest.mark.parametrize('size,refuse',[(0,True),(1,False),(3,False),(9,False),(10,True)])
def test_complete_fixed_pool_bound_is_generic_and_predeclared(size,refuse):
    source=module().prepare_driver_source();tree=ast.parse(source)
    conditions=[n.test for n in tree.body if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp)
                and 'len(pool)' in ast.unparse(n.test) and 'len(requests)' in ast.unparse(n.test)]
    assert len(conditions)==1
    assert eval(compile(ast.Expression(conditions[0]),'<pure-declared-pool-bound>','eval'),
                {'len':len,'pool':[None]*size,'requests':[None]*size}) is refuse
