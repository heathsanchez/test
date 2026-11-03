
#[cfg(test)]
mod captured_native_subtraction_tests {
 use super::*;
 use crate::nat::BigNat;
 fn number(n:&str)->BigNat{BigNat::parse_decimal(n).unwrap()}
 fn primitives()->NatPrimitives{NatPrimitives{type_name:NameId(1),type_expr:ExprId(20),zero:NameId(2),succ:NameId(3),recursor:NameId(4),add:None,mul:None,pow:None,land:None,shift_right:None,div:None,modulo:None,sub:Some(NameId(5)),pred:Some(NameId(6)),virtual_bvar_zero:Some(ExprId(0)),ble:None,beq:None}}
 fn expressions()->IdTable<ExprId,Expr>{
  let mut es=IdTable::default();
  for(id,e)in [(0,Expr::BVar(0)),(1,Expr::NatLit(number("0"))),(2,Expr::NatLit(number("1"))),(3,Expr::NatLit(number("5"))),(4,Expr::NatLit(number("2"))),(5,Expr::Const{name:NameId(6),levels:vec![]}),(6,Expr::App{fun:ExprId(5),arg:ExprId(0)}),(7,Expr::Const{name:NameId(5),levels:vec![]}),(8,Expr::App{fun:ExprId(7),arg:ExprId(3)}),(9,Expr::App{fun:ExprId(8),arg:ExprId(4)}),(10,Expr::App{fun:ExprId(0),arg:ExprId(1)}),(11,Expr::Lam{domain:ExprId(20),body:ExprId(6)}),(12,Expr::App{fun:ExprId(11),arg:ExprId(0)}),(20,Expr::Const{name:NameId(1),levels:vec![]}),(25,Expr::Const{name:NameId(3),levels:vec![]}),(26,Expr::App{fun:ExprId(25),arg:ExprId(0)})]{es.insert(ExprId(id),e).unwrap();}es
 }
 fn captured(a:u64,b:u64)->Closure{
  let value=Neutral{head:NeutralHead::Const{name:NameId(5),levels:vec![]},spine:vec![Closure::new(ExprId(a),EnvFrame::empty()),Closure::new(ExprId(b),EnvFrame::empty())]};
  Closure::new(ExprId(6),EnvFrame::empty().extend_neutral(value))
 }
 #[test]fn captured_subtraction_resumes_before_predecessor(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  for(a,b,want)in[(1,1,"0"),(3,4,"2"),(4,3,"0")]{let result=m.expose(captured(a,b),Transparency::Reducible,128);assert_eq!(result.proven_value(),Some(&Value::NatLit(number(want))),"{result:?}");}
 }

 fn raw(neutral:Neutral)->Closure{Closure::new(ExprId(0),EnvFrame::empty().extend_neutral(neutral))}
 fn subtraction(a:Closure,b:Closure)->Neutral{Neutral{head:NeutralHead::Const{name:NameId(5),levels:vec![]},spine:vec![a,b]}}
 fn closed(id:u64)->Closure{Closure::new(ExprId(id),EnvFrame::empty())}
 #[test]fn indirect_beta_capture_preserves_subtraction_order(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  let n=subtraction(closed(3),closed(4));let source=Closure::new(ExprId(12),EnvFrame::empty().extend_neutral(n));
  assert_eq!(m.expose(source,Transparency::Reducible,128).proven_value(),Some(&Value::NatLit(number("2"))));
 }
 #[test]fn replay_requires_registered_head_universes_arity_and_no_pending_argument(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  let valid=subtraction(closed(1),closed(1));let mut wrong_head=valid.clone();wrong_head.head=NeutralHead::Const{name:NameId(99),levels:vec![]};
  let mut wrong_universe=valid.clone();wrong_universe.head=NeutralHead::Const{name:NameId(5),levels:vec![crate::level::LevelTerm::Zero]};
  let mut short=valid.clone();short.spine.pop();let mut long=valid.clone();long.spine.push(closed(1));
  for n in [wrong_head,wrong_universe,short,long]{let r=m.expose(raw(n.clone()),Transparency::Reducible,128);assert_eq!(r.proven_value(),Some(&Value::Neutral(n)),"{r:?}");}
  let applied=Closure::new(ExprId(10),EnvFrame::empty().extend_neutral(valid.clone()));let mut expected=valid;expected.spine.push(Closure::new(ExprId(1),applied.env.clone()));
  assert_eq!(m.expose(applied,Transparency::Reducible,128).proven_value(),Some(&Value::Neutral(expected)));
 }
 #[test]fn low_fuel_then_high_fuel_matches_fresh_and_symbolic_stays_symbolic(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  let term=captured(1,1);let low=m.expose(term.clone(),Transparency::Reducible,2);assert!(!matches!(low.proven_value(),Some(Value::NatLit(_))));
  let high=m.expose(term.clone(),Transparency::Reducible,128);let fresh=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache()).expose(term,Transparency::Reducible,128);
  assert_eq!(high.proven_value(),Some(&Value::NatLit(number("0"))));assert_eq!(high.proven_value(),fresh.proven_value());
  let symbolic=subtraction(Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(9))),closed(2));
  assert_eq!(m.expose(raw(symbolic.clone()),Transparency::Reducible,128).proven_value(),Some(&Value::Neutral(symbolic)));
 }
 #[test]fn cached_incomplete_predecessor_cannot_bypass_replay(){
  let es=expressions();let ls=IdTable::default();let cache=new_exposure_cache();let term=captured(1,1);
  let stale=Value::Neutral(Neutral{head:NeutralHead::Const{name:NameId(6),levels:vec![]},spine:vec![Closure::new(ExprId(0),term.env.clone())]});
  let key=Rc::new(CachedExposureKey::new((AuthorityId(1),term.clone(),Transparency::Reducible,false,vec![])));cache.borrow_mut().retain_exposure(key,&stale,||true);
  let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(cache);
  assert_eq!(m.expose(term,Transparency::Reducible,128).proven_value(),Some(&Value::NatLit(number("0"))));
 }
 #[test]fn source_frames_and_authorities_are_not_merged(){
  let es=expressions();let ls=IdTable::default();let cache=new_exposure_cache();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(cache.clone());
  assert_eq!(m.expose(captured(3,4),Transparency::Reducible,128).proven_value(),Some(&Value::NatLit(number("2"))));
  assert_eq!(m.expose(captured(4,3),Transparency::Reducible,128).proven_value(),Some(&Value::NatLit(number("0"))));
  let n=subtraction(closed(3),closed(4));let source=raw(n.clone());assert_eq!(m.expose(source.clone(),Transparency::Reducible,128).proven_value(),Some(&Value::NatLit(number("3"))));
  let mut unregistered=primitives();unregistered.sub=None;let other=Machine::new(AuthorityId(2),&es,&ls,HashMap::new()).with_nat_primitives(Some(unregistered)).with_exposure_cache(cache);
  assert_eq!(other.expose(source,Transparency::Reducible,128).proven_value(),Some(&Value::Neutral(n)));
 }
 #[test]fn deep_captured_subtractions_terminate_without_guessing_a_numeral(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  let mut term=closed(1);for _ in 0..200{term=raw(subtraction(closed(1),term));}
  let r=m.expose(term,Transparency::Reducible,1024);assert!(r.is_unknown()||matches!(r.proven_value(),Some(Value::Neutral(_))),"{r:?}");
 }

 #[test]fn completed_predecessor_replay_uses_only_computed_numerals(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  for(a,b,want)in[(1,1,"0"),(3,4,"2"),(4,3,"0")]{let source=captured(a,b);let n=Neutral{head:NeutralHead::Const{name:NameId(6),levels:vec![]},spine:vec![Closure::new(ExprId(0),source.env)]};let r=m.qualified_nat_predecessor_result(&n,256);assert_eq!(r.proven_value(),Some(&Value::NatLit(number(want))),"{r:?}");}
 }
 #[test]fn predecessor_replay_declines_wrong_authority_shape_universe_and_tiny_fuel(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  let good=Neutral{head:NeutralHead::Const{name:NameId(6),levels:vec![]},spine:vec![closed(1)]};let mut wrong=good.clone();wrong.head=NeutralHead::Const{name:NameId(99),levels:vec![]};let mut universe=good.clone();universe.head=NeutralHead::Const{name:NameId(6),levels:vec![crate::level::LevelTerm::Zero]};let mut short=good.clone();short.spine.clear();let mut long=good.clone();long.spine.push(closed(1));
  for n in [wrong,universe,short,long]{assert!(m.qualified_nat_predecessor_result(&n,256).is_unknown());}
  assert!(m.qualified_nat_predecessor_result(&good,31).is_unknown());let mut missing=primitives();missing.pred=None;let other=Machine::new(AuthorityId(2),&es,&ls,HashMap::new()).with_nat_primitives(Some(missing));assert!(other.qualified_nat_predecessor_result(&good,256).is_unknown());
 }
 #[test]fn predecessor_replay_preserves_existing_fuel_and_declines_symbolic_results(){
  let es=expressions();let ls=IdTable::default();let m=Machine::new(AuthorityId(1),&es,&ls,HashMap::new()).with_nat_primitives(Some(primitives())).with_exposure_cache(new_exposure_cache());
  let n=Neutral{head:NeutralHead::Const{name:NameId(6),levels:vec![]},spine:vec![closed(1)]};m.exposure_fuel.set(Some(1));assert!(m.qualified_nat_predecessor_result(&n,256).is_unknown());assert_eq!(m.exposure_fuel.get(),Some(0));m.exposure_fuel.set(None);
  for id in [0,26]{let n=Neutral{head:NeutralHead::Const{name:NameId(6),levels:vec![]},spine:vec![Closure::new(ExprId(id),EnvFrame::empty().extend_free(FreeId(99)))]};assert!(m.qualified_nat_predecessor_result(&n,256).is_unknown());}
 }
}
