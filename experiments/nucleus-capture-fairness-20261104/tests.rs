
#[cfg(test)]
mod capture_fairness_tests {
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment,ExprId,ExprId){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(1))),(1,Expr::Const{name:NameId(1),levels:vec![]}),(2,Expr::Const{name:NameId(2),levels:vec![]}),(3,Expr::Const{name:NameId(3),levels:vec![]})]{e.insert(ExprId(id),node).unwrap();}
  let mut domain=ExprId(1);let mut argument=ExprId(2);let mut next=4;
  for _ in 0..96{e.insert(ExprId(next),Expr::Pi{domain:ExprId(1),body:domain}).unwrap();domain=ExprId(next);next+=1;e.insert(ExprId(next),Expr::Lam{domain:ExprId(1),body:argument}).unwrap();argument=ExprId(next);next+=1;}
  let mut roots=vec![];
  for body in[ExprId(2),ExprId(3)]{let fun=ExprId(next);e.insert(fun,Expr::Lam{domain,body}).unwrap();next+=1;let app=ExprId(next);e.insert(app,Expr::App{fun,arg:argument}).unwrap();next+=1;roots.push(app);}
  let env=Environment::empty().extend(NameId(1),crate::environment::ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(2),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(3),crate::environment::ConstantDecl::axiom(vec![],ExprId(1))).unwrap();
  (e,l,env,roots[0],roots[1])
 }
 #[test]fn failed_optional_capture_walk_leaves_work_for_ordinary_beta(){
  let(e,l,env,good,_)=fixture();let checker=TypeChecker::new(&e,&l,&env);
  let left=TypeValue::Term(Closure::new(good,EnvFrame::empty().extend_free(FreeId(7))));let right=TypeValue::Term(Closure::new(good,EnvFrame::empty().extend_free(FreeId(9))));
  assert!(crate::convert::convert_with_policy_in_context(&checker,&left,&right,128,crate::convert::DeltaPolicy::PreferredOnly,0,&[]).is_proven());
 }
 #[test]fn preserved_reduction_budget_does_not_identify_different_results(){
  let(e,l,env,good,bad)=fixture();let checker=TypeChecker::new(&e,&l,&env);
  let left=TypeValue::Term(Closure::new(good,EnvFrame::empty().extend_free(FreeId(7))));let right=TypeValue::Term(Closure::new(bad,EnvFrame::empty().extend_free(FreeId(9))));
  assert!(!crate::convert::convert_with_policy_in_context(&checker,&left,&right,128,crate::convert::DeltaPolicy::PreferredOnly,0,&[]).is_proven());
 }
}
