
#[cfg(test)]
mod capture_pair_memo_tests{
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){
  let mut e=IdTable::default();for(id,x)in[(0,Expr::BVar(0)),(1,Expr::BVar(1)),(2,Expr::App{fun:ExprId(1),arg:ExprId(0)}),(3,Expr::Sort(LevelId(0))),(4,Expr::Lam{domain:ExprId(3),body:ExprId(1)}),(5,Expr::Lam{domain:ExprId(3),body:ExprId(5)})]{e.insert(ExprId(id),x).unwrap();}
  let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();(e,l,Environment::empty())
 }
 fn chain(free:u64)->Closure{let mut c=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(free)));for _ in 0..12{c=Closure::new(ExprId(0),EnvFrame::empty().extend(c));}c}
 fn term(free:u64)->Closure{Closure::new(ExprId(2),EnvFrame::empty().extend(chain(free)).extend(chain(9)))}
 #[test]fn a_completed_capture_pair_reuses_its_proof_at_a_small_paid_allowance(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let a=term(7);let b=term(7);assert!(c.exact_source_capture_identity(&a,&b,&mut 4096));assert!(c.exact_source_capture_identity(&a,&b,&mut 4));assert!(!c.exact_source_capture_identity(&a,&b,&mut 0));}
 #[test]fn retained_pairs_do_not_erase_actual_free_universe_or_source_differences(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let a=term(7);let b=term(7);assert!(c.exact_source_capture_identity(&a,&b,&mut 4096));for wrong in [term(8),Closure::with_levels(b.expr,b.env.clone(),LevelSubstitution::new(vec![(NameId(7),LevelTerm::Zero)])),Closure::new(ExprId(1),b.env.clone())]{assert!(!c.exact_source_capture_identity(&a,&wrong,&mut 4096));}assert!(c.exact_source_capture_identity(&a,&b,&mut 4));}
 #[test]fn failed_or_exhausted_work_never_becomes_a_capture_proof(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let a=term(7);let b=term(7);assert!(!c.exact_source_capture_identity(&a,&b,&mut 4));assert!(!c.exact_source_capture_identity(&a,&b,&mut 4));assert!(!c.exact_source_capture_identity(&a,&term(8),&mut 4096));assert!(!c.exact_source_capture_identity(&a,&term(8),&mut 4));for _ in 0..2{assert!(!c.exact_source_capture_identity(&Closure::new(ExprId(5),EnvFrame::empty().extend_free(FreeId(7))),&Closure::new(ExprId(5),EnvFrame::empty().extend_free(FreeId(7))),&mut 128));}}
 #[test]fn capture_proofs_do_not_cross_checker_source_authority(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let a=term(7);let b=term(7);assert!(c.exact_source_capture_identity(&a,&b,&mut 4096));let other=TypeChecker::new(&e,&l,&env);assert!(!other.exact_source_capture_identity(&a,&b,&mut 4));}
}
