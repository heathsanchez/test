import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from webarena_blind_matrix import partition, failure_class

class AccountingTests(unittest.TestCase):
 def test_every_site_combination_has_one_lane(self):
  for name in ('reddit','gitlab','shopping','shopping_admin'):
   self.assertEqual(partition([name]),name)
  for sites in (['reddit','gitlab'],['map','wikipedia'],['wikipedia','gitlab'],[]):
   self.assertEqual(partition(sites),'crosssite')

 def test_unsupported_route_is_distinct_from_a_browser_failure(self):
  for message in ('ValueError: unsupported shopping instruction: x', 'RuntimeError: no blind route for intent: x'):
   self.assertEqual(failure_class(message),'unsupported_route')
  self.assertEqual(failure_class('ValueError: unsupported initial site: __MAP__'),'unsupported_site')
  self.assertEqual(failure_class('TimeoutError: Locator.click failed'),'execution_error')
  self.assertEqual(failure_class('ValueError: invalid price amount'),'execution_error')

if __name__=='__main__':unittest.main()

class ScorerBoundaryTests(unittest.TestCase):
 def test_dict_dataset_uses_typed_authority_and_opaque_paths(self):
  import json, tempfile, types
  from unittest.mock import patch
  from webarena_blind_matrix import run_lane
  seen=[]
  class Config:
   @staticmethod
   def from_file(path):return {}
  class Authority:
   def __init__(self,config):pass
   def get_task(self,ident):
    seen.append(ident)
    return types.SimpleNamespace(eval=[])
   def evaluate_task(self,**kwargs):
    return types.SimpleNamespace(score=1.0,status=types.SimpleNamespace(value='success'),model_dump=lambda **kw:{'score':1})
  class Trace:
   @staticmethod
   def model_construct(**kwargs):return types.SimpleNamespace(evaluation_events=[])
  modules={
   'webarena_verified.api':types.SimpleNamespace(WebArenaVerified=Authority),
   'webarena_verified.types.config':types.SimpleNamespace(WebArenaVerifiedConfig=Config),
   'webarena_verified.types.tracing':types.SimpleNamespace(NetworkTrace=Trace),
  }
  def agent(command,out,timeout):
   self.assertNotIn('--task-id',command)
   self.assertEqual(len(out.name),32)
   (out/'agent_response.json').write_text(json.dumps({'task_type':'RETRIEVE','status':'SUCCESS','retrieved_data':[0]}))
   return 0
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);data=root/'input.json'
   data.write_text(json.dumps([{'task_id':i,'sites':['shopping'],'intent':'read','start_urls':['__SHOPPING__']} for i in range(258)]))
   with patch.dict(sys.modules,modules),patch('webarena_blind_matrix.invoke_agent',side_effect=agent):
    report=run_lane(data,'shopping',root/'out')
   self.assertEqual(report['scorer_errors'],0)
   self.assertEqual(report['official_success_count'],258)
   self.assertEqual(len(seen),258)
