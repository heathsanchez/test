//! A recursor is not injective in its unselected minor premises.
//! Both applications select C0; changing only the C1 branch must not block
//! conversion. This fixture supplies an explicit, well-typed two-constructor
//! elimination table; declaration admission is outside this unit boundary.
use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::machine::{Machine, RecursorReduction, RecursorRule, Transparency};
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame};

struct Terms { table: IdTable<ExprId, Expr>, next: u64 }
impl Terms {
    fn put(&mut self, e: Expr) -> ExprId {
        let id=ExprId(self.next); self.next+=1; self.table.insert(id,e).unwrap(); id
    }
    fn var(&mut self,n:u64)->ExprId { self.put(Expr::BVar(n)) }
    fn app(&mut self,f:ExprId,a:ExprId)->ExprId { self.put(Expr::App{fun:f,arg:a}) }
    fn lam(&mut self,d:ExprId,b:ExprId)->ExprId { self.put(Expr::Lam{domain:d,body:b}) }
    fn pi(&mut self,d:ExprId,b:ExprId)->ExprId { self.put(Expr::Pi{domain:d,body:b}) }
    fn constant(&mut self,n:u64)->ExprId { self.put(Expr::Const{name:NameId(n),levels:vec![]}) }
    fn apps(&mut self,mut f:ExprId,args:&[ExprId])->ExprId {
        for a in args { f=self.app(f,*a); } f
    }
}

fn check_case(change_selected: bool) {
    let mut t=Terms{table:IdTable::default(),next:0};
    let mut levels=IdTable::default();
    levels.insert(LevelId(0),Level::Zero).unwrap();
    levels.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
    let sort=t.put(Expr::Sort(LevelId(1)));
    let b=t.constant(100); let c0=t.constant(101); let c1=t.constant(102);
    let rec=t.constant(103); let hidden=t.constant(104);
    let v0=t.var(0); let v1=t.var(1); let v2=t.var(2); let v3=t.var(3);
    let motive_ty=t.pi(b,sort);
    let m_c0=t.app(v0,c0);
    let m_c1=t.app(v1,c1);
    let m_x=t.app(v3,v0);
    let final_pi=t.pi(b,m_x);
    let minor1_pi=t.pi(m_c1,final_pi);
    let minor0_pi=t.pi(m_c0,minor1_pi);
    let rec_ty=t.pi(motive_ty,minor0_pi);
    // rhs0 = fun motive minor0 minor1 => minor0; rhs1 returns minor1.
    let r0_inner=t.lam(m_c1,v1); let r0_mid=t.lam(m_c0,r0_inner);
    let rhs0=t.lam(motive_ty,r0_mid);
    let r1_inner=t.lam(m_c1,v0); let r1_mid=t.lam(m_c0,r1_inner);
    let rhs1=t.lam(motive_ty,r1_mid);
    let motive=t.lam(b,b);
    let left=t.apps(rec,&[motive,c0,c0,hidden]);
    let right=t.apps(rec,&[motive,if change_selected {c1}else{c0},c1,hidden]);
    let mut env=Environment::empty();
    for (n,d) in [
        (100,ConstantDecl::inductive_type(vec![],sort)),
        (101,ConstantDecl::constructor(vec![],b)),
        (102,ConstantDecl::constructor(vec![],b)),
        (103,ConstantDecl::recursor(vec![],rec_ty)),
        (104,ConstantDecl::definition(vec![],b,c0,false)),
    ] { env=env.extend(NameId(n),d).unwrap(); }
    env=env.install_recursor_reduction(NameId(103),RecursorReduction{
        k:false,num_params:0,num_indices:0,level_params:vec![],
        rules:vec![
            RecursorRule{constructor:NameId(101),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:rhs0},
            RecursorRule{constructor:NameId(102),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:rhs1},
        ],
    }).unwrap();
    let closure=|id| Closure::new(id,EnvFrame::empty());
    let machine=Machine::new(env.authority(),&t.table,&levels,env.definition_bodies())
        .with_recursor_reductions(env.recursor_reductions());
    let lhs=machine.expose(closure(left),Transparency::Full,2048);
    let rhs=machine.expose(closure(right),Transparency::Full,2048);
    assert!(lhs.is_proven() && rhs.is_proven(),"{lhs:?}; {rhs:?}");
    assert_eq!(lhs.proven_value()==rhs.proven_value(),!change_selected,
        "explicit iota independently fixes the expected result");
    let checker=TypeChecker::new(&t.table,&levels,&env);
    let result=checker.convert(&TypeValue::Term(closure(left)),&TypeValue::Term(closure(right)),2048);
    if change_selected {
        assert!(!result.is_proven(),"different selected results cannot merge");
    } else {
        assert!(result.is_proven(),"equal recursor results rejected after a failed argument probe: {result:?}");
    }
    let _=v2;
}

#[test]
fn different_unselected_minors_do_not_block_recursor_conversion() { check_case(false); }
#[test]
fn different_selected_minors_remain_distinguishable() { check_case(true); }
