use metatron_kernel::convert::DeltaPolicy;
use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame};

struct Fixture { es:IdTable<ExprId,Expr>, ls:IdTable<LevelId,Level>, env:Environment, left:ExprId, right:ExprId }
struct Build { es:IdTable<ExprId,Expr>, next:u64 }
impl Build {
 fn put(&mut self,e:Expr)->ExprId { let id=ExprId(self.next);self.next+=1;self.es.insert(id,e).unwrap();id }
 fn c(&mut self,n:u64)->ExprId {self.put(Expr::Const{name:NameId(n),levels:vec![]})}
 fn app(&mut self,f:ExprId,a:ExprId)->ExprId {self.put(Expr::App{fun:f,arg:a})}
 fn lam(&mut self,d:ExprId,b:ExprId)->ExprId {self.put(Expr::Lam{domain:d,body:b})}
}
impl Fixture {
 fn new(data:bool,different:bool,hidden:bool,scoped:bool)->Self {
  let mut b=Build{es:IdTable::default(),next:0};
  let prop=b.put(Expr::Sort(LevelId(0)));let ty=b.put(Expr::Sort(LevelId(1)));
  let a=b.c(1);let x=b.c(2);let y=b.c(3);let p=b.c(4);let alias=b.c(5);
  let v0=b.put(Expr::BVar(0));let v1=b.put(Expr::BVar(1));
  let identity=b.lam(a,v0);let beta=b.app(identity,x);
  let pty=b.put(Expr::Pi{domain:a,body:if data{ty}else{prop}});
  let left_ty=b.app(p,if hidden{alias}else{beta});let right_ty=b.app(p,if different{y}else{x});
  let mut env=Environment::empty();
  for (n,t) in [(1,ty),(2,a),(3,a),(4,pty),(6,left_ty),(7,right_ty)] {env=env.extend(NameId(n),ConstantDecl::axiom(vec![],t)).unwrap();}
  env=env.extend(NameId(5),ConstantDecl::definition(vec![],a,x,false)).unwrap();
  let (left,right)=if scoped {
   let first=b.app(p,v0);let beta_local=b.app(identity,v1);let second=b.app(p,if different{y}else{beta_local});
   let l=b.lam(second,v1);let l=b.lam(first,l);let l=b.lam(a,l);
   let r=b.lam(second,v0);let r=b.lam(first,r);let r=b.lam(a,r);(l,r)
  } else {(b.c(6),b.c(7))};
  let mut ls=IdTable::default();ls.insert(LevelId(0),Level::Zero).unwrap();ls.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  Self{es:b.es,ls,env,left,right}
 }
 fn check(&self,policy:DeltaPolicy,budget:usize)->bool {
  TypeChecker::new(&self.es,&self.ls,&self.env).convert_with_policy(
   &TypeValue::Term(Closure::new(self.left,EnvFrame::empty())),
   &TypeValue::Term(Closure::new(self.right,EnvFrame::empty())),budget,policy).is_proven()
 }
}
#[test] fn convertible_proposition_types_allow_proof_irrelevance() {
 assert!(Fixture::new(false,false,false,false).check(DeltaPolicy::GuardedSemanticFallback,2048));
}
#[test] fn convertible_data_types_do_not_erase_data() {
 assert!(!Fixture::new(true,false,false,false).check(DeltaPolicy::GuardedSemanticFallback,2048));
}
#[test] fn different_propositions_do_not_erase_proofs() {
 assert!(!Fixture::new(false,true,false,false).check(DeltaPolicy::GuardedSemanticFallback,2048));
}
#[test] fn proof_type_conversion_retains_caller_delta_policy() {
 let f=Fixture::new(false,false,true,false);
 assert!(!f.check(DeltaPolicy::PreferredOnly,2048));
 assert!(f.check(DeltaPolicy::GuardedSemanticFallback,2048));
}
#[test] fn dependent_local_proofs_keep_their_typed_scope() {
 assert!(Fixture::new(false,false,false,true).check(DeltaPolicy::GuardedSemanticFallback,4096));
 assert!(!Fixture::new(false,true,false,true).check(DeltaPolicy::GuardedSemanticFallback,4096));
}
#[test] fn exhausted_budget_grants_no_equality() {
 assert!(!Fixture::new(false,false,false,false).check(DeltaPolicy::GuardedSemanticFallback,0));
}

#[test]
fn nested_proof_type_conversion_cannot_reset_its_permission() {
 let mut f=Fixture::new(false,false,false,false);
 assert!(f.check(DeltaPolicy::GuardedSemanticFallback,4096));
 let domain=f.env.get(NameId(7)).unwrap().ty;
 let prop=ExprId(1000);f.es.insert(prop,Expr::Sort(LevelId(0))).unwrap();
 let rty=ExprId(1001);f.es.insert(rty,Expr::Pi{domain,body:prop}).unwrap();
 f.env=f.env.extend(NameId(8),ConstantDecl::axiom(vec![],rty)).unwrap();
 let r=ExprId(1002);f.es.insert(r,Expr::Const{name:NameId(8),levels:vec![]}).unwrap();
 for (id,name,arg) in [(1003,9,f.left),(1005,10,f.right)] {
  let ty=ExprId(id);f.es.insert(ty,Expr::App{fun:r,arg}).unwrap();
  f.env=f.env.extend(NameId(name),ConstantDecl::axiom(vec![],ty)).unwrap();
  f.es.insert(ExprId(id+1),Expr::Const{name:NameId(name),levels:vec![]}).unwrap();
 }
 f.left=ExprId(1004);f.right=ExprId(1006);
 // The propositions R p and R q need the new rule again to compare p and q.
 // This deliberately bounded extension declines that nested obligation.
 assert!(!f.check(DeltaPolicy::GuardedSemanticFallback,10000));
}

#[test]
fn proposition_probe_cap_survives_a_large_outer_budget() {
 let mut f=Fixture::new(false,false,false,false);
 let original_ty=f.env.get(NameId(6)).unwrap().ty;
 let Expr::App{fun:family,arg:beta}=f.es.get(original_ty).unwrap().clone() else {panic!("fixture");};
 let Expr::App{fun:identity,arg:mut body}=f.es.get(beta).unwrap().clone() else {panic!("fixture");};
 for i in 1000..1512 {let next=ExprId(i);f.es.insert(next,Expr::App{fun:identity,arg:body}).unwrap();body=next;}
 let ty=ExprId(1512);f.es.insert(ty,Expr::App{fun:family,arg:body}).unwrap();
 f.env=f.env.extend(NameId(8),ConstantDecl::axiom(vec![],ty)).unwrap();
 f.left=ExprId(1513);f.es.insert(f.left,Expr::Const{name:NameId(8),levels:vec![]}).unwrap();
 assert!(!f.check(DeltaPolicy::GuardedSemanticFallback,1_000_000));
}
