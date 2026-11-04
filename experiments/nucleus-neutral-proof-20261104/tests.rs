
 #[test]fn distinct_checked_constant_proofs_of_the_same_negation_convert(){
  let(mut e,l,env)=source();e.insert(ExprId(65),Expr::Const{name:NameId(707),levels:vec![]}).unwrap();
  e.insert(ExprId(66),Expr::App{fun:ExprId(65),arg:ExprId(25)}).unwrap();
  let env=env.extend(NameId(707),ConstantDecl::theorem(vec![],ExprId(67))).unwrap();
  e.insert(ExprId(67),Expr::Pi{domain:ExprId(0),body:ExprId(11)}).unwrap();
  let checker=TypeChecker::new(&e,&l,&env);let(ctx,frame)=context(&checker,0);
  let left=TypeValue::Term(Closure::new(ExprId(32),frame.clone()));let right=TypeValue::Term(Closure::new(ExprId(66),frame));
  assert!(crate::convert::convert_with_policy_in_context(&checker,&left,&right,4096,crate::convert::DeltaPolicy::GuardedSemanticFallback,ctx.len(),&ctx).is_proven());
 }
