use metatron_kernel::verdict::Verdict;
use serde_json::{Value, json};
use std::collections::HashMap;
use std::io::Cursor;

fn witness() -> Vec<Value> {
    include_str!("fixtures/good-list-perm-v434.ndjson")
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}
fn run(rows: Vec<Value>) -> Verdict {
    let bytes = rows
        .into_iter()
        .map(|row| row.to_string() + "\n")
        .collect::<String>();
    metatron_kernel::run(Cursor::new(bytes.as_bytes()))
}

#[test]
fn recursive_prop_contract_is_independent_of_the_family_name() {
    let mut rows = witness();
    for row in &mut rows {
        if row["str"]["str"] == "Perm" {
            row["str"]["str"] = json!("RenamedPermutationWitness");
        }
    }
    assert_eq!(run(rows), Verdict::Accept);
}

#[test]
fn recursive_prop_refuses_a_rule_that_drops_recursive_calls() {
    let mut rows = witness();
    let block = rows.last_mut().unwrap();
    block["inductive"]["recs"][0]["rules"][1]["rhs"] =
        block["inductive"]["recs"][0]["rules"][0]["rhs"].clone();
    assert_ne!(run(rows), Verdict::Accept);
}

#[test]
fn recursive_prop_refuses_false_index_metadata() {
    let mut rows = witness();
    rows.last_mut().unwrap()["inductive"]["recs"][0]["numIndices"] = json!(1);
    assert_ne!(run(rows), Verdict::Accept);
}

#[test]
fn recursive_prop_refuses_large_elimination_even_with_unchanged_metadata() {
    let mut rows = witness();
    let rec_type = rows.last().unwrap()["inductive"]["recs"][0]["type"]
        .as_u64()
        .unwrap();
    let outer = rows.iter().find(|r| r["ie"] == rec_type).unwrap()["forallE"]["body"]
        .as_u64()
        .unwrap();
    let mut motive = rows.iter().find(|r| r["ie"] == outer).unwrap()["forallE"]["type"]
        .as_u64()
        .unwrap();
    loop {
        let row = rows.iter().find(|r| r["ie"] == motive).unwrap();
        let body = row["forallE"]["body"].as_u64().unwrap();
        let body_row = rows.iter().find(|r| r["ie"] == body).unwrap();
        if body_row.get("sort").is_some() {
            break;
        }
        motive = body;
    }
    // Expr 0 is Sort u in the pinned witness; alter only the motive result.
    rows.iter_mut().find(|r| r["ie"] == motive).unwrap()["forallE"]["body"] = json!(0);
    assert_ne!(run(rows), Verdict::Accept);
}

#[test]
fn recursive_prop_refuses_a_false_nonrecursive_annotation() {
    let mut rows = witness();
    rows.last_mut().unwrap()["inductive"]["types"][0]["isRec"] = json!(false);
    assert_ne!(run(rows), Verdict::Accept);
}

#[test]
fn recursive_prop_refuses_out_of_range_variables_without_panicking() {
    let mut rows = witness();
    let ctor_type = rows.last().unwrap()["inductive"]["ctors"][1]["type"]
        .as_u64()
        .unwrap();
    let fresh_id = rows.iter().filter_map(|r| r["ie"].as_u64()).max().unwrap() + 1;
    let insert = rows.len() - 1;
    rows.insert(insert, json!({"ie": fresh_id, "bvar": u64::MAX}));
    rows.iter_mut().find(|r| r["ie"] == ctor_type).unwrap()["forallE"]["type"] = json!(fresh_id);
    assert_ne!(run(rows), Verdict::Accept);
}

#[test]
fn admitted_recursive_prop_rules_execute_cons_and_both_trans_hypotheses() {
    use metatron_kernel::id::{ExprId, LevelId};
    use metatron_kernel::machine::{
        AuthorityId, Machine, RecursorReduction, RecursorRule, Transparency,
    };
    use metatron_kernel::parser::parse;
    use metatron_kernel::syntax::{Declaration, Expr, Level};
    use metatron_kernel::value::{Closure, EnvFrame, FreeId, NeutralHead, Value as RuntimeValue};
    assert_eq!(run(witness()), Verdict::Accept);
    let mut export = parse(Cursor::new(include_bytes!(
        "fixtures/good-list-perm-v434.ndjson"
    )))
    .unwrap()
    .resolve()
    .unwrap();
    let Declaration::Inductive(block) = export.declarations.last().unwrap() else {
        panic!("missing block")
    };
    let block = block.clone();
    let rec = &block.recursors[0];
    let levels = rec
        .level_params
        .iter()
        .map(|name| {
            LevelId(
                export
                    .levels
                    .iter_raw()
                    .find(|(_, level)| matches!(level,Level::Param(n) if n==name))
                    .unwrap()
                    .0,
            )
        })
        .collect::<Vec<_>>();
    let mut next = export.exprs.iter_raw().map(|(id, _)| id).max().unwrap() + 1;
    let mut insert = |expr| {
        let id = ExprId(next);
        next += 1;
        export.exprs.insert(id, expr).unwrap();
        id
    };
    let vars = (0..8).map(|i| insert(Expr::BVar(i))).collect::<Vec<_>>();
    let mut applied = |name, args: &[ExprId]| {
        let mut f = insert(Expr::Const {
            name,
            levels: levels.clone(),
        });
        for arg in args {
            f = insert(Expr::App { fun: f, arg: *arg });
        }
        f
    };
    let nil = applied(block.constructors[0].name, &[vars[0]]);
    let cons = applied(
        block.constructors[1].name,
        &[vars[0], vars[6], vars[7], vars[7], nil],
    );
    let trans = applied(
        block.constructors[3].name,
        &[vars[0], vars[7], vars[7], vars[7], cons, cons],
    );
    let call = applied(
        rec.name,
        &[
            vars[0], vars[1], vars[2], vars[3], vars[4], vars[5], vars[7], vars[7], trans,
        ],
    );
    let reduction = RecursorReduction {
        k: false,
        num_params: rec.num_params as usize,
        num_indices: rec.num_indices as usize,
        level_params: rec.level_params.clone(),
        rules: rec
            .rules
            .iter()
            .map(|rule| RecursorRule {
                constructor: rule.constructor,
                constructor_level_params: Vec::new(),
                num_params: rec.num_params as usize,
                num_fields: rule.num_fields as usize,
                rhs: rule.rhs,
            })
            .collect(),
    };
    let machine = Machine::new(
        AuthorityId(0),
        &export.exprs,
        &export.levels,
        HashMap::new(),
    )
    .with_recursor_reductions(HashMap::from([(rec.name, reduction)]));
    let env = (0..8)
        .rev()
        .fold(EnvFrame::empty(), |env, i| env.extend_free(FreeId(100 + i)));
    let substitution = metatron_kernel::value::LevelSubstitution::new(
        rec.level_params
            .iter()
            .map(|name| (*name, metatron_kernel::level::LevelTerm::Zero))
            .collect(),
    );
    let result = machine.expose(
        Closure::with_levels(call, env, substitution),
        Transparency::Opaque,
        2048,
    );
    let Some(RuntimeValue::Neutral(trans_result)) = result.proven_value() else {
        panic!("{result:?}")
    };
    assert_eq!(trans_result.head, NeutralHead::Free(FreeId(105)));
    assert_eq!(trans_result.spine.len(), 7);
    for hypothesis in &trans_result.spine[5..] {
        let result = machine.expose(hypothesis.clone(), Transparency::Opaque, 2048);
        let Some(RuntimeValue::Neutral(cons_result)) = result.proven_value() else {
            panic!("{result:?}")
        };
        assert_eq!(cons_result.head, NeutralHead::Free(FreeId(103)));
        assert_eq!(cons_result.spine.len(), 5);
        let result = machine.expose(cons_result.spine[4].clone(), Transparency::Opaque, 2048);
        let Some(RuntimeValue::Neutral(nil_result)) = result.proven_value() else {
            panic!("{result:?}")
        };
        assert_eq!(nil_result.head, NeutralHead::Free(FreeId(102)));
        assert!(nil_result.spine.is_empty());
    }
}
