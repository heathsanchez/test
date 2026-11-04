#[cfg(test)]
mod source_projection_template_tests {
 use super::*;
 use crate::environment::ConstantDecl;
 fn source(projected_owner:NameId)->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,n)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Const{name:NameId(900),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::Proj{type_name:projected_owner,index:0,structure:ExprId(3)}),(5,Expr::Lam{domain:ExprId(2),body:ExprId(4)})]{e.insert(ExprId(id),n).unwrap();}(e,l)
 }
 // These tests certify only literal syntax discovery. Layout and typing
 // authority are independently required by the caller before eta reduction.
 fn base()->Environment{Environment::empty().extend(NameId(900),ConstantDecl::axiom(vec![],ExprId(1))).unwrap()}
 fn with_projector(env:&Environment)->Environment{env.extend(NameId(905),ConstantDecl::definition(vec![],ExprId(0),ExprId(5),true)).unwrap()}
 #[test]fn completed_literal_projection_fact_reuses_at_a_small_paid_allowance(){
  let(e,l)=source(NameId(900));let env=with_projector(&base());let checker=TypeChecker::new(&e,&l,&env);let mut cold=512;
  assert_eq!(checker.checked_source_projection_template(NameId(900),0,&mut cold),Some(ExprId(4)));let mut warm=8;
  assert_eq!(checker.checked_source_projection_template(NameId(900),0,&mut warm),Some(ExprId(4)));assert!(warm<8);
 }
 #[test]fn cached_projection_fact_never_bypasses_current_source_shape(){
  let(e,l)=source(NameId(900));let env=with_projector(&base());let checker=TypeChecker::new(&e,&l,&env);let mut fuel=512;assert!(checker.checked_source_projection_template(NameId(900),0,&mut fuel).is_some());
  let(changed,ll)=source(NameId(901));let other=TypeChecker::new(&changed,&ll,&env);let mut fuel=512;assert!(other.checked_source_projection_template(NameId(900),0,&mut fuel).is_none());
 }
 #[test]fn a_future_projector_definition_does_not_justify_an_earlier_scope(){
  let(e,l)=source(NameId(900));let early=base();let late=with_projector(&early);let checker=TypeChecker::new(&e,&l,&late);let mut fuel=512;assert!(checker.checked_source_projection_template(NameId(900),0,&mut fuel).is_some());
  let earlier=TypeChecker::new(&e,&l,&early);let mut fuel=512;assert!(earlier.checked_source_projection_template(NameId(900),0,&mut fuel).is_none());let mut fuel=8;assert!(checker.checked_source_projection_template(NameId(900),0,&mut fuel).is_some());
 }
 #[test]fn unfinished_template_search_retains_no_absence_certificate(){
  let(e,l)=source(NameId(900));let env=with_projector(&base());let checker=TypeChecker::new(&e,&l,&env);let mut tiny=1;assert!(checker.checked_source_projection_template(NameId(900),0,&mut tiny).is_none());assert!(env.cached_source_projection_template(NameId(900),0).is_none());
  let mut enough=512;assert_eq!(checker.checked_source_projection_template(NameId(900),0,&mut enough),Some(ExprId(4)));
 }
 #[test]fn a_completed_source_fact_can_be_used_without_unpaid_memo_growth(){
  let mut witnessed=false;
  for budget in 1..64{
   let(e,l)=source(NameId(900));let env=with_projector(&base());let checker=TypeChecker::new(&e,&l,&env);let mut fuel=budget;
   if checker.checked_source_projection_template(NameId(900),0,&mut fuel)==Some(ExprId(4))&&env.cached_source_projection_template(NameId(900),0).is_none(){witnessed=true;break;}
  }
  assert!(witnessed,"optional retention must not withhold a completed literal source fact");
 }

}
