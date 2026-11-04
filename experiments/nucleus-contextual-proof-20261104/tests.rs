#[cfg(test)]
mod contextual_negation_proof_tests {
 use super::*;
 use crate::environment::ConstantDecl;
 fn source()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,n)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::BVar(0)),(3,Expr::BVar(1)),(4,Expr::BVar(2)),(5,Expr::BVar(3)),(6,Expr::Const{name:NameId(701),levels:vec![]}),(7,Expr::Pi{domain:ExprId(2),body:ExprId(6)}),(8,Expr::Lam{domain:ExprId(0),body:ExprId(7)}),(9,Expr::Pi{domain:ExprId(0),body:ExprId(0)}),(10,Expr::Const{name:NameId(702),levels:vec![]}),(11,Expr::App{fun:ExprId(10),arg:ExprId(2)}),(12,Expr::App{fun:ExprId(10),arg:ExprId(3)}),(13,Expr::App{fun:ExprId(10),arg:ExprId(4)}),(14,Expr::App{fun:ExprId(10),arg:ExprId(5)}),(15,Expr::Pi{domain:ExprId(13),body:ExprId(14)}),(16,Expr::Pi{domain:ExprId(12),body:ExprId(15)}),(17,Expr::Pi{domain:ExprId(11),body:ExprId(16)}),(18,Expr::Pi{domain:ExprId(0),body:ExprId(17)}),(19,Expr::Const{name:NameId(703),levels:vec![]}),(20,Expr::Pi{domain:ExprId(13),body:ExprId(19)}),(21,Expr::Pi{domain:ExprId(12),body:ExprId(20)}),(22,Expr::Pi{domain:ExprId(11),body:ExprId(21)}),(23,Expr::Pi{domain:ExprId(0),body:ExprId(22)}),(24,Expr::Const{name:NameId(700),levels:vec![]}),(25,Expr::BVar(18)),(26,Expr::BVar(17)),(27,Expr::BVar(16)),(28,Expr::BVar(15)),(29,Expr::App{fun:ExprId(24),arg:ExprId(25)}),(30,Expr::App{fun:ExprId(29),arg:ExprId(26)}),(31,Expr::App{fun:ExprId(30),arg:ExprId(27)}),(32,Expr::App{fun:ExprId(31),arg:ExprId(28)}),(33,Expr::BVar(6)),(34,Expr::Const{name:NameId(704),levels:vec![]}),(35,Expr::App{fun:ExprId(34),arg:ExprId(25)}),(36,Expr::App{fun:ExprId(35),arg:ExprId(26)}),(37,Expr::App{fun:ExprId(36),arg:ExprId(27)}),(38,Expr::App{fun:ExprId(37),arg:ExprId(28)})]{e.insert(ExprId(id),n).unwrap();}
  for(id,n)in[
   (42,Expr::Const{name:NameId(705),levels:vec![]}),(43,Expr::Const{name:NameId(706),levels:vec![]}),
   (44,Expr::Pi{domain:ExprId(11),body:ExprId(0)}),(45,Expr::Pi{domain:ExprId(0),body:ExprId(44)}),
   (46,Expr::App{fun:ExprId(42),arg:ExprId(3)}),(47,Expr::App{fun:ExprId(46),arg:ExprId(2)}),
   (48,Expr::Pi{domain:ExprId(47),body:ExprId(13)}),(49,Expr::Pi{domain:ExprId(11),body:ExprId(48)}),(50,Expr::Pi{domain:ExprId(0),body:ExprId(49)}),
   (51,Expr::BVar(16)),(52,Expr::BVar(15)),(53,Expr::BVar(14)),(54,Expr::BVar(13)),
   (55,Expr::App{fun:ExprId(24),arg:ExprId(51)}),(56,Expr::App{fun:ExprId(55),arg:ExprId(52)}),(57,Expr::App{fun:ExprId(56),arg:ExprId(53)}),(58,Expr::App{fun:ExprId(57),arg:ExprId(54)}),
   (59,Expr::App{fun:ExprId(42),arg:ExprId(51)}),(60,Expr::App{fun:ExprId(59),arg:ExprId(58)}),
   (61,Expr::App{fun:ExprId(43),arg:ExprId(25)}),(62,Expr::App{fun:ExprId(61),arg:ExprId(33)}),(63,Expr::BVar(1)),(64,Expr::App{fun:ExprId(62),arg:ExprId(63)})
  ]{e.insert(ExprId(id),n).unwrap();}
  let env=Environment::empty().extend(NameId(701),ConstantDecl::axiom(vec![],ExprId(0))).unwrap().extend(NameId(702),ConstantDecl::definition(vec![],ExprId(9),ExprId(8),true)).unwrap().extend(NameId(700),ConstantDecl::theorem(vec![],ExprId(18))).unwrap().extend(NameId(703),ConstantDecl::axiom(vec![],ExprId(1))).unwrap().extend(NameId(704),ConstantDecl::axiom(vec![],ExprId(23))).unwrap();(e,l,env.extend(NameId(705),ConstantDecl::axiom(vec![],ExprId(45))).unwrap().extend(NameId(706),ConstantDecl::axiom(vec![],ExprId(50))).unwrap())
 }
 fn context(checker:&TypeChecker<'_>,kind:u8)->(Vec<TypeValue>,EnvFrame){
  let mut ctx=vec![TypeValue::Sort(LevelTerm::Zero)];let mut frame=EnvFrame::empty().extend_free(FreeId(0));checker.retain_checked_binding(&frame,ctx[0].clone(),&ctx);
  let neg=TypeValue::Term(Closure::new(ExprId(11),frame.clone()));let prop=TypeValue::Term(Closure::new(ExprId(2),frame.clone()));let data=TypeValue::Term(Closure::new(ExprId(19),EnvFrame::empty()));
  for i in 1..19 {let ty=if i==17&&kind==3{TypeValue::Term(Closure::new(ExprId(60),frame.clone()))}else if i==12&&kind==1{prop.clone()}else if i==12&&kind==2{data.clone()}else{neg.clone()};frame=frame.extend_free(FreeId(i));ctx.push(ty.clone());checker.retain_checked_binding(&frame,ty,&ctx);}(ctx,frame)
 }
 #[test]fn four_argument_negation_proof_and_actual_local_convert_in_nineteen_binders(){
  let(e,l,env)=source();let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,0);
  let left=TypeValue::Term(Closure::new(ExprId(32),frame.clone()));let right=TypeValue::Term(Closure::new(ExprId(33),frame));
  let result=crate::convert::convert_with_policy_in_context(&checker,&left,&right,4096,crate::convert::DeltaPolicy::GuardedSemanticFallback,ctx.len(),&ctx);
  assert!(result.is_proven(),"both independently checked terms prove the same negation: {result:?}");
 }
 #[test]fn proof_of_a_different_proposition_cannot_be_erased_as_the_same_proof(){
  let(e,l,env)=source();let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,1);
  assert!(!checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(32),frame.clone()),&Closure::new(ExprId(33),frame),&ctx,4096));
 }
 #[test]fn nonproof_data_with_a_four_argument_head_keeps_its_identity(){
  let(e,l,env)=source();let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,2);
  assert!(!checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(38),frame.clone()),&Closure::new(ExprId(33),frame),&ctx,4096));
 }
 #[test]fn wider_proof_admission_requires_the_full_bounded_allowance(){
  let(e,l,env)=source();let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,0);
  for budget in [0,255,256,512,1023] {assert!(!checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(32),frame.clone()),&Closure::new(ExprId(33),frame.clone()),&ctx,budget));}
 }
 #[test]fn wrong_proof_argument_cannot_supply_a_checked_proof(){
  let(mut e,l,env)=source();e.insert(ExprId(39),Expr::App{fun:ExprId(29),arg:ExprId(25)}).unwrap();
  e.insert(ExprId(40),Expr::App{fun:ExprId(39),arg:ExprId(27)}).unwrap();e.insert(ExprId(41),Expr::App{fun:ExprId(40),arg:ExprId(28)}).unwrap();
  let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,0);
  assert!(!checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(41),frame.clone()),&Closure::new(ExprId(33),frame),&ctx,4096));
 }

 #[test]fn nested_prerequisite_cannot_reenter_wider_proof_admission(){
  let(e,l,env)=source();let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,3);
  assert!(!checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(64),frame.clone()),&Closure::new(ExprId(33),frame.clone()),&ctx,4096),"outer proof must not recursively license its own argument conversion");
  assert!(checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(32),frame.clone()),&Closure::new(ExprId(33),frame),&ctx,4096),"completed trial must restore independent proof admission");
 }

 #[test]fn active_wider_trial_cannot_license_nested_proof_conversion_and_restores_scope(){
  let(e,l,env)=source();let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,0);
  let trial=WideProofTrial::enter().unwrap();
  assert!(!checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(32),frame.clone()),&Closure::new(ExprId(33),frame.clone()),&ctx,4096));
  assert!(WideProofTrial::enter().is_none());drop(trial);
  assert!(checker.checked_proof_vs_local_in_context(&Closure::new(ExprId(32),frame.clone()),&Closure::new(ExprId(33),frame),&ctx,4096));
 }

}
