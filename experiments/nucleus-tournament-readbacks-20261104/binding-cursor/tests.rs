
#[cfg(test)]
mod sorted_capture_binding_tests{
 use super::*;
 fn fixture()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>,Environment){let mut e=IdTable::default();for(id,x)in[(0,Expr::BVar(0)),(1,Expr::BVar(1)),(2,Expr::BVar(2)),(3,Expr::BVar(3)),(4,Expr::App{fun:ExprId(1),arg:ExprId(2)}),(5,Expr::App{fun:ExprId(4),arg:ExprId(3)}),(6,Expr::BVar(4))]{e.insert(ExprId(id),x).unwrap();}(e,IdTable::default(),Environment::empty())}
 fn frame()->EnvFrame{EnvFrame::empty().extend_free(FreeId(7)).extend_free(FreeId(8)).extend_free(FreeId(9))}
 #[test]fn sorted_used_captures_share_a_single_paid_environment_prefix(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);assert_eq!(c.complete_source_support(ExprId(5),&mut 4096),Some(vec![1,2,3]));let body=Closure::new(ExprId(5),frame());assert!(crate::convert::source_opening_avoids_capture(&c,&body,FreeId(0),&mut 9));}
 #[test]fn a_middle_used_binding_still_exposes_a_real_free_collision(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let body=Closure::new(ExprId(5),frame());assert!(!crate::convert::source_opening_avoids_capture(&c,&body,FreeId(8),&mut 4096));}
 #[test]fn an_unbound_used_slot_is_not_confused_with_the_virtual_binder(){let(e,l,env)=fixture();let c=TypeChecker::new(&e,&l,&env);let frame=frame();let absent=Closure::new(ExprId(6),frame.clone());assert!(!crate::convert::source_opening_avoids_capture(&c,&absent,FreeId(0),&mut 128));let internal=Closure::new(ExprId(0),frame);assert!(crate::convert::source_opening_avoids_capture(&c,&internal,FreeId(0),&mut 128));}
 #[test]fn traversed_but_unused_slots_do_not_claim_capture_authority(){let(mut e,l,env)=fixture();e.insert(ExprId(7),Expr::App{fun:ExprId(1),arg:ExprId(3)}).unwrap();let c=TypeChecker::new(&e,&l,&env);let body=Closure::new(ExprId(7),frame());assert!(crate::convert::source_opening_avoids_capture(&c,&body,FreeId(8),&mut 4096),"unused middle binding is traversed but not used");for free in[7,9]{assert!(!crate::convert::source_opening_avoids_capture(&c,&body,FreeId(free),&mut 4096),"both used endpoints must still be checked");}}

}
