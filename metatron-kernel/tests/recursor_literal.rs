use metatron_kernel::environment::NatPrimitives;
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::judgment::Judgment;
use metatron_kernel::machine::{
    AuthorityId, Machine, RecursorReduction, RecursorRule, Transparency,
};
use metatron_kernel::nat::BigNat;
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::value::{Closure, EnvFrame, NeutralHead, Value};
use std::collections::HashMap;

struct Terms {
    es: IdTable<ExprId, Expr>,
    next: u64,
}
impl Terms {
    fn put(&mut self, e: Expr) -> ExprId {
        let id = ExprId(self.next);
        self.next += 1;
        self.es.insert(id, e).unwrap();
        id
    }
    fn var(&mut self, n: u64) -> ExprId {
        self.put(Expr::BVar(n))
    }
    fn app(&mut self, f: ExprId, a: ExprId) -> ExprId {
        self.put(Expr::App { fun: f, arg: a })
    }
    fn lam(&mut self, b: ExprId) -> ExprId {
        self.put(Expr::Lam {
            domain: ExprId(0),
            body: b,
        })
    }
    fn lams(&mut self, mut b: ExprId, n: usize) -> ExprId {
        for _ in 0..n {
            b = self.lam(b);
        }
        b
    }
}

// The supplied reduction table stands for independently admitted Nat rules.
// Rule RHSs are ordinary expressions; no runtime natural-number function is trusted.
fn run(
    n: &str,
    take_ih: bool,
    authority: Option<NameId>,
    transparency: Transparency,
    extra: bool,
    fuel: usize,
) -> Judgment<Value> {
    let mut t = Terms {
        es: IdTable::default(),
        next: 0,
    };
    let prop = t.put(Expr::Sort(LevelId(0)));
    let rec = t.put(Expr::Const {
        name: NameId(30),
        levels: vec![],
    });
    let lit = t.put(Expr::NatLit(BigNat::parse_decimal(n).unwrap()));
    let z = t.var(1);
    let zero_rhs = t.lams(z, 3);
    let mot = t.var(3);
    let z = t.var(2);
    let s = t.var(1);
    let pred = t.var(0);
    let recursive = t.app(rec, mot);
    let recursive = t.app(recursive, z);
    let recursive = t.app(recursive, s);
    let recursive = t.app(recursive, pred);
    let body = t.app(s, pred);
    let body = t.app(body, recursive);
    let succ_rhs = t.lams(body, 4);
    let step_body = t.var(if take_ih { 0 } else { 1 });
    let step = t.lams(step_body, 2);
    let base = if extra {
        let b = t.var(0);
        t.lam(b)
    } else {
        prop
    };
    let call = t.app(rec, prop);
    let call = t.app(call, base);
    let call = t.app(call, step);
    let call = t.app(call, lit);
    let call = if extra { t.app(call, prop) } else { call };
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    let nat = authority.map(|recursor| NatPrimitives {
        type_name: NameId(1),
        type_expr: prop,
        zero: NameId(10),
        succ: NameId(11),
        recursor,
        add: None,
        sub: None,
        ble: None,
    });
    let machine = Machine::new(AuthorityId(0), &t.es, &levels, HashMap::new())
        .with_nat_primitives(nat)
        .with_recursor_reductions(HashMap::from([(
            NameId(30),
            RecursorReduction {
                eq_k: false,
                num_params: 0,
                num_indices: 0,
                level_params: vec![],
                rules: vec![
                    RecursorRule {
                        constructor: NameId(10),
                        num_params: 0,
                        num_fields: 0,
                        rhs: zero_rhs,
                    },
                    RecursorRule {
                        constructor: NameId(11),
                        num_params: 0,
                        num_fields: 1,
                        rhs: succ_rhs,
                    },
                ],
            },
        )]));
    machine.expose(Closure::new(call, EnvFrame::empty()), transparency, fuel)
}

#[test]
fn literal_zero_uses_certified_zero_rule() {
    assert!(matches!(
        run(
            "0",
            false,
            Some(NameId(30)),
            Transparency::Full,
            false,
            1024
        )
        .proven_value(),
        Some(Value::Sort(_))
    ));
}
#[test]
fn literal_successor_supplies_predecessor_absent_from_expression_table() {
    for (n, p) in [
        ("1", "0"),
        ("100", "99"),
        (
            "123456789012345678901234567890",
            "123456789012345678901234567889",
        ),
    ] {
        assert_eq!(
            run(n, false, Some(NameId(30)), Transparency::Full, false, 1024).proven_value(),
            Some(&Value::NatLit(BigNat::parse_decimal(p).unwrap()))
        );
    }
}
#[test]
fn literal_recursion_consumes_induction_result_and_preserves_pending_application() {
    for n in ["0", "1", "9"] {
        assert!(matches!(
            run(n, true, Some(NameId(30)), Transparency::Full, true, 4096).proven_value(),
            Some(Value::Sort(_))
        ));
    }
}
#[test]
fn literal_view_requires_nat_authority_and_full_exposure() {
    for (authority, transparency) in [
        (None, Transparency::Full),
        (Some(NameId(31)), Transparency::Full),
        (Some(NameId(30)), Transparency::Opaque),
        (Some(NameId(30)), Transparency::Reducible),
    ] {
        assert!(
            matches!(run("1",false,authority,transparency,false,1024).proven_value(),Some(Value::Neutral(n)) if matches!(n.head,NeutralHead::Const{name:NameId(30),..}) && n.spine.len()==4)
        );
    }
}
#[test]
fn huge_recursive_literal_exhausts_fuel_without_a_verdict() {
    assert!(matches!(
        run(
            "123456789012345678901234567890",
            true,
            Some(NameId(30)),
            Transparency::Full,
            false,
            256
        ),
        Judgment::Unknown { .. }
    ));
}

#[test]
fn actual_nat_boolean_matcher_prefix_checks() {
    assert_eq!(
        metatron_kernel::run(std::io::Cursor::new(include_str!(
            "fixtures/nat_literal_matcher_prefix.ndjson"
        ))),
        metatron_kernel::verdict::Verdict::Accept
    );
}
