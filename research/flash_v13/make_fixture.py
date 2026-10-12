from pathlib import Path
import json
v={
 'version':'flash-v13-20261012',
 'scope':'SYNTHETIC FINITE DEPENDENCY GRAPH; source-bound capabilities are labelled but cross-links are simulated',
 'source_authorities':{
 'v10':{'repo':'heathsanchez/test','run':38199516805,'claim':'bounded six-matroid guarded greedy-transfer; no stateless superiority'},
 'v11':{'repo':'heathsanchez/test','run':38201499353,'claim':'bounded complete hereditary branch rule; weighted objective unsupported'},
 'v12':{'repo':'heathsanchez/test','run':38202495321,'claim':'bounded source-selected modular-weight optimizer; 6/6 fresh weighted; 3/3 unsupported abstentions'}},
 'base_facts':['always','source_archive','source_access','resources_safe','external_verifier','matroid_scope_guard','hereditary_scope_guard','verified_v10','verified_v11','verified_v12','v12_direct','available_stateless','protected_equivalence','goal_future'],
 'rules':[
  {'id':i,'when':w,'then':o} for i,w,o in [
 ('matroid',['verified_v10','matroid_scope_guard'],'cap_greedy'),
 ('hereditary',['verified_v11','hereditary_scope_guard'],'cap_complete'),
 ('modular_direct',['verified_v12','v12_direct'],'cap_weighted'),
 ('modular_lineage',['verified_v12','verified_v11'],'cap_weighted'),
 ('revival',['cap_greedy','new_future_requires_structure'],'cap_revived'),
 ('sensor',['event_sensor','source_access'],'cap_sensor'),
 ('viability',['event_viability','resources_safe'],'cap_viability'),
 ('joint',['cap_sensor','cap_viability'],'cap_joint'),
 ('genesis',['cap_joint','cap_complete','external_verifier'],'cap_genesis'),
 ('merged',['protected_equivalence','goal_future'],'cap_merged'),
 ('split',['event_separator','source_access'],'cap_split'),
 ('sep_reuse',['cap_split','cap_sensor'],'cap_sep_reuse'),
 ('advanced',['cap_genesis','cap_sep_reuse'],'cap_advanced'),
 ('weighted_safe',['cap_weighted','cap_viability'],'cap_weighted_safe'),
 ('frontier_cross',['cap_advanced','cap_weighted_safe'],'cap_frontier_cross'),
 ('unrelated',['event_unrelated'],'cap_unused')]],
 'frontiers':[
 {'id':'F_matroid','budget':15,'options':[
 {'id':'source_qualified_greedy','when':['cap_greedy'],'unless':[],'cost':3},
 {'id':'complete_fallback','when':['cap_complete'],'unless':[],'cost':9}]},
 {'id':'F_nonmatroid','budget':14,'options':[
 {'id':'source_checked_complete','when':['cap_complete'],'unless':[],'cost':8},
 {'id':'stateless_safe','when':['available_stateless'],'unless':[],'cost':12}]},
 {'id':'F_weighted','budget':14,'options':[
 {'id':'compiled_modular','when':['cap_weighted'],'unless':[],'cost':5},
 {'id':'independent_stateless','when':['available_stateless'],'unless':[],'cost':13}]},
 {'id':'F_dormant_reuse','budget':10,'options':[
 {'id':'repurposed_greedy','when':['cap_revived'],'unless':[],'cost':3}]},
 {'id':'F_observation','budget':10,'options':[
 {'id':'constructive_sensor','when':['cap_sensor'],'unless':[],'cost':6}]},
 {'id':'F_joint_genesis','budget':12,'options':[
 {'id':'safe_generated','when':['cap_genesis'],'unless':[],'cost':6},
 {'id':'old_expensive','when':['cap_complete'],'unless':[],'cost':20}]},
 {'id':'F_quotient','budget':10,'options':[
 {'id':'merged','when':['cap_merged'],'unless':['event_separator'],'cost':1},
 {'id':'split','when':['cap_split'],'unless':[],'cost':3}]},
 {'id':'F_dependent_search','budget':10,'options':[
 {'id':'construction_with_separator','when':['cap_advanced'],'unless':[],'cost':5}]},
 {'id':'F_weighted_viability','budget':8,'options':[
 {'id':'viable_modular','when':['cap_weighted_safe'],'unless':[],'cost':5}]},
 {'id':'F_scope_obstruction','budget':10,'options':[
 {'id':'old_assumption','when':['cap_greedy'],'unless':['event_nonmatroid_obstruction'],'cost':1},
 {'id':'repaired_scope','when':['cap_complete'],'unless':[],'cost':4}]},
 {'id':'F_cross_capability','budget':10,'options':[
 {'id':'joint_warranted','when':['cap_frontier_cross'],'unless':[],'cost':2}]},
 {'id':'F_unrelated_control','budget':4,'options':[
 {'id':'constant','when':['always'],'unless':[],'cost':1}]},
 {'id':'F_unreachable','budget':3,'options':[
 {'id':'unsupported','when':['never_verified'],'unless':[],'cost':1}]}],
 'allowed_events':{
 'promote':['event_sensor','event_viability','new_future_requires_structure','event_separator','event_nonmatroid_obstruction','event_unrelated','verified_v11','verified_v10','verified_v12','protected_equivalence','v12_direct'],
 'revoke':['event_sensor','event_viability','new_future_requires_structure','event_separator','event_nonmatroid_obstruction','event_unrelated','verified_v11','verified_v10','verified_v12','protected_equivalence','v12_direct']},
 'events': [
 {'kind':a,'fact':b,'authority':c} for a,b,c in [
 ('promote','event_sensor','synthetic_event'),
 ('promote','event_viability','synthetic_event'),
 ('promote','new_future_requires_structure','synthetic_event'),
 ('promote','event_separator','synthetic_event'),
 ('promote','event_nonmatroid_obstruction','synthetic_event'),
 ('promote','event_unrelated','synthetic_event'),
 ('promote','event_sensor','synthetic_event'),
 ('revoke','verified_v11','synthetic_revoker'),
 ('revoke','v12_direct','synthetic_revoker'),
 ('promote','verified_v11','synthetic_event'),
 ('revoke','event_separator','synthetic_revoker'),
 ('revoke','verified_v10','synthetic_revoker'),
 ('promote','verified_v10','synthetic_event'),
 ('revoke','protected_equivalence','synthetic_revoker'),
 ('promote','protected_equivalence','synthetic_event'),
 ('revoke','verified_v12','synthetic_revoker'),
 ('promote','verified_v12','synthetic_event'),
 ('revoke','event_sensor','synthetic_revoker'),
 ('promote','event_sensor','synthetic_event')]],
 'restart_after_event_index':6,
 'adversarial_tests':[
 {'kind':'promote','fact':'uncatalogued','authority':'synthetic_event'},
 {'kind':'revoke','fact':'verified_v12','authority':'wrong_revoker'},
 {'kind':'promote','fact':'event_sensor','authority':'synthetic_revoker'}]
}
p=Path(__file__).with_name('fixture.json')
p.write_text(json.dumps(v,indent=2)+'\n')
print(p,p.stat().st_size)
