"""Local route selection guards; scientific execution is qualified separately."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from research.unified_consequence_runtime.developmental_machine import Machine


class NativeFrontierActivationTests(unittest.TestCase):
    def machine(self,operation='native.source_patch',request=None):
        m=object.__new__(Machine)
        m.descriptor=Mock(return_value=SimpleNamespace(operation=operation,
            scope={'target':'cachetools','families':['B','C']}))
        m.get=Mock(return_value=request or {'subject':'cachetools'})
        return m

    def route(self,**updates):
        return {'status':'READY','capability_id':'selected-by-flash','request':'content-hash',
                'profile':'cachetools:protected-observer',**updates}

    @patch('research.unified_consequence_runtime.cross_frontier.require_frontier_route')
    def test_missing_route_never_constructs_or_executes(self,route):
        machine=self.machine()
        runtime=SimpleNamespace(machine=machine,_validated=Mock(),execute=Mock())
        route.return_value=self.route(status='UNKNOWN_SEARCH',capability_id=None)
        self.assertEqual(machine.select_and_execute_frontier('missing',runtime)['status'],'UNKNOWN_SEARCH')
        runtime.execute.assert_not_called()

    @patch('research.unified_consequence_runtime.cross_frontier.require_frontier_route')
    def test_wrong_subject_cannot_reuse_matching_profile(self,route):
        machine=self.machine(request={'subject':'boltons'})
        runtime=SimpleNamespace(machine=machine,_validated=Mock(),execute=Mock())
        route.return_value=self.route()
        with self.assertRaisesRegex(ValueError,'request differs'):
            machine.select_and_execute_frontier('cachetools:protected-observer',runtime)
        runtime.execute.assert_not_called()

    @patch('research.unified_consequence_runtime.cross_frontier.require_frontier_route')
    def test_wrong_observation_family_cannot_execute(self,route):
        machine=self.machine('flash.native_observation',{'family':'A'})
        runtime=SimpleNamespace(machine=machine,_validated=Mock(),execute=Mock())
        route.return_value=self.route(profile='tomlkit:A')
        with self.assertRaisesRegex(ValueError,'request differs'):
            machine.select_and_execute_frontier('tomlkit:A',runtime)
        runtime.execute.assert_not_called()

    def test_other_warrant_state_cannot_supply_adapter(self):
        machine=self.machine()
        runtime=SimpleNamespace(machine=object(),_validated=Mock(),execute=Mock())
        with self.assertRaisesRegex(ValueError,'different warrant state'):
            machine.select_and_execute_frontier('frontier',runtime)
        runtime.execute.assert_not_called()

    @patch('research.unified_consequence_runtime.cross_frontier.require_frontier_route')
    def test_execution_uses_selected_existing_capability(self,route):
        machine=self.machine()
        runtime=SimpleNamespace(machine=machine,_validated=Mock(),execute=Mock(return_value=({'native':'checked'},'receipt')))
        route.return_value=self.route()
        result=machine.select_and_execute_frontier('frontier',runtime)
        runtime.execute.assert_called_once_with('selected-by-flash')
        self.assertEqual(result['consequence'],'receipt')
        self.assertEqual(result['new_constructor_invocations'],0)


if __name__=='__main__':unittest.main()
