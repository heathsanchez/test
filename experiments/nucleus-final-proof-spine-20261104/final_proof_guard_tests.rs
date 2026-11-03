#[cfg(test)]
mod final_proof_guard_tests {
 use super::*;
 fn setup()->(IdTable<ExprId,Expr>,IdTable<LevelId,crate::syntax::Level>,Environment){
  use crate::syntax::Level;use crate::environment::ConstantDecl;
  let mut es=IdTable::default();let mut ls=IdTable::default();
  ls.insert(LevelId(0),Level::Zero).unwrap();ls.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();ls.insert(LevelId(2),Level::Param(NameId(9))).unwrap();
  es.insert(ExprId(0),Expr::Sort(LevelId(2))).unwrap();
  es.insert(ExprId(1),Expr::Const{name:NameId(1),levels:vec![LevelId(2)]}).unwrap();
  es.insert(ExprId(2),Expr::Const{name:NameId(2),levels:vec![LevelId(2)]}).unwrap();
  for(id,name,level)in [(3,3,0),(4,4,0),(5,5,0),(6,4,1),(7,3,1)]{
   es.insert(ExprId(id),Expr::Const{name:NameId(name),levels:vec![LevelId(level)]}).unwrap();
  }
  let mut env=Environment::empty();
  for(name,ty)in [(1,0),(2,0),(3,1),(4,1),(5,2)]{
   env=env.extend_owned(NameId(name),ConstantDecl::axiom(vec![NameId(9)],ExprId(ty))).unwrap();
  }(es,ls,env)
 }
 fn term(id:u64)->Closure{Closure::new(ExprId(id),EnvFrame::empty())}
 #[test]fn distinct_independently_formed_propositions_do_not_license_proof_equality(){
  let(es,ls,env)=setup();let checker=TypeChecker::new(&es,&ls,&env);let ctx=vec![TypeValue::Sort(LevelTerm::Zero);4];
  assert!(checker.checked_proof_pair_in_bounded_context(&term(3),&term(4),&ctx,2048));
  assert!(!checker.checked_proof_pair_in_bounded_context(&term(3),&term(5),&ctx,2048));
 }
 #[test]fn both_universe_instantiated_types_must_be_propositions(){
  let(es,ls,env)=setup();let checker=TypeChecker::new(&es,&ls,&env);let ctx=vec![TypeValue::Sort(LevelTerm::Zero);4];
  assert!(!checker.checked_proof_pair_in_bounded_context(&term(7),&term(4),&ctx,2048));
  assert!(!checker.checked_proof_pair_in_bounded_context(&term(3),&term(6),&ctx,2048));
  assert!(!checker.checked_proof_pair_in_bounded_context(&term(7),&term(6),&ctx,2048));
 }
 #[test]fn bounded_trial_declines_below_its_explicit_entry_budget(){
  let(es,ls,env)=setup();let checker=TypeChecker::new(&es,&ls,&env);let ctx=vec![TypeValue::Sort(LevelTerm::Zero);4];
  assert!(!checker.checked_proof_pair_in_bounded_context(&term(3),&term(4),&ctx,512));
 }
}
#[cfg(test)]mod final_proof_capture_guard_tests{
 use super::*;
 #[test]fn used_captures_cannot_be_identified_by_shared_source_syntax(){
  use crate::environment::ConstantDecl;use crate::syntax::Level;
  let mut es=IdTable::default();let mut ls=IdTable::default();ls.insert(LevelId(0),Level::Zero).unwrap();ls.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  let mut push=|e|{let id=ExprId(es.len() as u64);es.insert(id,e).unwrap();id};
  let sort=push(Expr::Sort(LevelId(1)));let c=push(Expr::Const{name:NameId(1),levels:vec![]});let prop=push(Expr::Sort(LevelId(0)));let b=push(Expr::BVar(0));
  let rel=push(Expr::Const{name:NameId(2),levels:vec![]});let rb=push(Expr::App{fun:rel,arg:b});let rbb=push(Expr::App{fun:rb,arg:b});
  let rtail=push(Expr::Pi{domain:c,body:prop});let rty=push(Expr::Pi{domain:c,body:rtail});let pty=push(Expr::Pi{domain:c,body:rbb});
  let p=push(Expr::Const{name:NameId(3),levels:vec![]});let q=push(Expr::Const{name:NameId(4),levels:vec![]});let pa=push(Expr::App{fun:p,arg:b});let qa=push(Expr::App{fun:q,arg:b});drop(push);
  let mut env=Environment::empty();for(name,ty)in [(1,sort),(2,rty),(3,pty),(4,pty)]{env=env.extend_owned(NameId(name),ConstantDecl::axiom(vec![],ty)).unwrap();}
  let checker=TypeChecker::new(&es,&ls,&env);let ctx=vec![TypeValue::Term(Closure::new(c,EnvFrame::empty()));4];
  let a=EnvFrame::empty().extend_free(FreeId(0));let a_again=EnvFrame::empty().extend_free(FreeId(0));let b=EnvFrame::empty().extend_free(FreeId(1));
  assert!(checker.checked_proof_pair_in_bounded_context(&Closure::new(pa,a.clone()),&Closure::new(qa,a_again),&ctx,2048));
  assert!(!checker.checked_proof_pair_in_bounded_context(&Closure::new(pa,a),&Closure::new(qa,b),&ctx,2048));
 }
}
