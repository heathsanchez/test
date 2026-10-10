//! Read-only source-bound symbolic definitional-equality probes.
//! Produces evidence, never installs reduction rules or changes a verdict.

use crate::environment::Environment;
use crate::id::{ExprId, IdTable, LevelId, NameId};
use crate::syntax::{Expr, Level};
use crate::typecheck::{TypeChecker, TypeValue};
use crate::value::{Closure, EnvFrame};

struct Builder<'a> {
    expressions: &'a mut IdTable<ExprId, Expr>,
    next: u64,
}
impl Builder<'_> {
    fn put(&mut self, e: Expr) -> ExprId {
        let idx = self.next.checked_add(1).expect("synthetic probe ExprId overflow");
        self.next = idx;
        let id = ExprId(idx);
        self.expressions.insert(id, e).expect("unique synthetic probe expression");
        id
    }
    fn app(&mut self, fun: ExprId, arg: ExprId) -> ExprId {
        self.put(Expr::App { fun, arg })
    }
    fn apply2(&mut self, fun: ExprId, x: ExprId, y: ExprId) -> ExprId {
        let first = self.app(fun,x);
        self.app(first,y)
    }
    fn lam(&mut self, domain: ExprId, body: ExprId) -> ExprId {
        self.put(Expr::Lam {domain, body})
    }
}
pub(crate) fn probe(
    expressions: &mut IdTable<ExprId, Expr>,
    levels: &IdTable<LevelId, Level>,
    environment: &Environment,
    mul_name: NameId,
    budget: usize,
) {
    let Some(nat) = environment.nat_primitives() else {return};
    let Some(add) = nat.add else {return};
    let mut b = Builder {
        next: expressions.iter_raw().map(|(id,_)|id).max().unwrap_or(0),
        expressions,
    };
    let n = b.put(Expr::BVar(0));
    let m = b.put(Expr::BVar(1));
    let mul = b.put(Expr::Const{name:mul_name,levels:vec![]});
    let zero = b.put(Expr::Const{name:nat.zero,levels:vec![]});
    let succ = b.put(Expr::Const{name:nat.succ,levels:vec![]});
    let plus = b.put(Expr::Const{name:add,levels:vec![]});
    let natty = nat.type_expr;

    let mul_n_zero = b.apply2(mul,n,zero);
    let lhs_zero = b.lam(natty,mul_n_zero);
    let rhs_zero = b.lam(natty,zero);

    let succ_m = b.app(succ,n);
    let mul_m_succ_n = b.apply2(mul,m,succ_m);
    let lhs_succ_inner = b.lam(natty,mul_m_succ_n);
    let lhs_succ = b.lam(natty,lhs_succ_inner);
    let mul_m_n = b.apply2(mul,m,n);
    let rhs_succ_body=b.apply2(plus,mul_m_n,m);
    let rhs_succ_inner=b.lam(natty,rhs_succ_body);
    let rhs_succ=b.lam(natty,rhs_succ_inner);

    let one=b.app(succ,zero);
    let mul_n_one=b.apply2(mul,n,one);
    let lhs_wrong=b.lam(natty,mul_n_one);
    let rhs_wrong=b.lam(natty,n);
    let zero_mul_n=b.apply2(mul,zero,n);
    let lhs_wrong2=b.lam(natty,zero_mul_n);

    // Borrow the now-complete expression table. Every candidate is a
    // closed lambda whose free input is supplied through a checked binder.
    let checker=TypeChecker::new(&*b.expressions,levels,environment);
    let cases=[
        ("mul_n_zero",lhs_zero,rhs_zero,true),
        ("mul_m_succ_n",lhs_succ,rhs_succ,true),
        ("incorrect_mul_n_one",lhs_wrong,rhs_wrong,false),
        ("incorrect_zero_mul_n",lhs_wrong2,rhs_zero,false),
    ];
    for (label,lhs,rhs,positive) in cases {
        let inferred_l=checker.infer(lhs,budget);
        let inferred_r=checker.infer(rhs,budget);
        let comparable=match (inferred_l.proven_value(),inferred_r.proven_value()){
            (Some(a),Some(b))=>checker.convert(a,b,budget),
            _=>crate::judgment::Judgment::unknown("synthetic-mul-inferred-type"),
        };
        let left=TypeValue::Term(Closure::new(lhs,EnvFrame::empty()));
        let right=TypeValue::Term(Closure::new(rhs,EnvFrame::empty()));
        let relation=if comparable.is_proven(){
            checker.convert(&left,&right,budget)
        }else{
            crate::judgment::Judgment::unknown("synthetic-mul-type-unverified")
        };
        eprintln!("NUCLEUS_MUL_DEFEQ_PROBE:label={label}:should_be_defeq={positive}:types={comparable:?}:relation={relation:?}:authority={:?}",
            environment.authority());
        // Even in diagnostics a contradiction to the protected negative
        // assumptions signals a material soundness concern. Never promote.
        if !positive && relation.is_proven(){
            eprintln!("NUCLEUS_MUL_DEFEQ_PROBE:NEGATIVE_VIOLATION:{label}");
        }
    }
}
