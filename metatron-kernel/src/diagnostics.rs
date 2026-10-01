//! Deterministic, feature-gated operation counters.
//!
//! These counters are evidence instruments, never semantic inputs.  They are
//! thread-local so parallel tests and independent checker calls do not share
//! observation state.  Normal Arena builds omit this module and every update.

use std::cell::{Cell, RefCell};
use std::collections::{HashMap, HashSet};

use crate::id::ExprId;

use crate::verdict::Verdict;

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct OperationCounts {
    pub declarations: u64,
    pub inductive_signatures: u64,
    pub type_judgments: u64,
    pub conversions: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DiagnosticRun {
    pub verdict: Verdict,
    pub operations: OperationCounts,
}

thread_local! {
    static DECLARATIONS: Cell<u64> = const { Cell::new(0) };
    static INDUCTIVE_SIGNATURES: Cell<u64> = const { Cell::new(0) };
    static TYPE_JUDGMENTS: Cell<u64> = const { Cell::new(0) };
    static CONVERSIONS: Cell<u64> = const { Cell::new(0) };
}

pub(crate) fn reset() {
    DECLARATIONS.set(0);
    INDUCTIVE_SIGNATURES.set(0);
    TYPE_JUDGMENTS.set(0);
    CONVERSIONS.set(0);
}

pub(crate) fn declaration() {
    causal_scope();
    DECLARATIONS.set(DECLARATIONS.get().saturating_add(1));
}

pub(crate) fn inductive_signature() {
    INDUCTIVE_SIGNATURES.set(INDUCTIVE_SIGNATURES.get().saturating_add(1));
}

pub(crate) fn type_judgment() {
    TYPE_JUDGMENTS.set(TYPE_JUDGMENTS.get().saturating_add(1));
}

pub(crate) fn conversion() {
    CONVERSIONS.set(CONVERSIONS.get().saturating_add(1));
}

pub(crate) fn snapshot() -> OperationCounts {
    OperationCounts {
        declarations: DECLARATIONS.get(),
        inductive_signatures: INDUCTIVE_SIGNATURES.get(),
        type_judgments: TYPE_JUDGMENTS.get(),
        conversions: CONVERSIONS.get(),
    }
}


// Causal evidence is output only. No return value enters a kernel judgment.
thread_local! {
    static CAUSAL_SCOPE: Cell<u64> = const { Cell::new(0) };
    static CAUSAL_EVENTS: Cell<u64> = const { Cell::new(0) };
    static INFERENCE_FRAMES: RefCell<HashMap<ExprId, HashSet<u64>>> =
        RefCell::new(HashMap::new());
}

pub(crate) fn causal_scope() {
    CAUSAL_SCOPE.set(CAUSAL_SCOPE.get().saturating_add(1));
    CAUSAL_EVENTS.set(0);
    INFERENCE_FRAMES.with(|frames| frames.borrow_mut().clear());
}

struct BoundedDebug {
    text: String,
    truncated: bool,
}
impl std::fmt::Write for BoundedDebug {
    fn write_str(&mut self, value: &str) -> std::fmt::Result {
        if self.text.len().saturating_add(value.len()) > 16384 {
            self.truncated = true;
            return Err(std::fmt::Error);
        }
        self.text.push_str(value);
        Ok(())
    }
}

pub(crate) fn inference_frame(expression: ExprId, frame: u64) -> Option<usize> {
    if std::env::var_os("NUCLEUS_TRACE_INFERENCE_FRAMES").is_none() {
        return None;
    }
    INFERENCE_FRAMES.with(|all| {
        let mut all = all.borrow_mut();
        let frames = all.entry(expression).or_default();
        if !frames.insert(frame) {
            return None;
        }
        let count = frames.len();
        if matches!(count, 16 | 64 | 256 | 1024 | 4096 | 16384) {
            eprintln!("NUCLEUS_INFERENCE_FRAME_MULTIPLICITY:{}", serde_json::json!({
                "scope": CAUSAL_SCOPE.get(),
                "expression": format!("{expression:?}"),
                "distinct_frames": count,
                "latest_frame": frame
            }));
            Some(count)
        } else {
            None
        }
    })
}

pub(crate) fn causal(kind: &str, detail: std::fmt::Arguments<'_>) {
    if std::env::var_os("NUCLEUS_TRACE_CAUSAL").is_none() {
        return;
    }
    let event = CAUSAL_EVENTS.get();
    if event > 32 {
        return;
    }
    CAUSAL_EVENTS.set(event + 1);
    let mut output = BoundedDebug { text: String::new(), truncated: false };
    let kind = if event == 32 { "trace-limit" } else { kind };
    if event < 32 {
        let _ = std::fmt::write(&mut output, detail);
    }
    eprintln!("NUCLEUS_CAUSAL:{}", serde_json::json!({
        "scope": CAUSAL_SCOPE.get(), "event": event, "kind": kind,
        "detail": output.text, "truncated": output.truncated || event == 32
    }));
}

/// Conservative preflight for a diagnostic call into the existing recursive
/// shape checker. Count occurrences (not unique nodes) to bound shared trees.
pub(crate) fn probe_expression_budget(
    expressions: &crate::id::IdTable<crate::id::ExprId, crate::syntax::Expr>,
    roots: &[crate::id::ExprId],
    max_work: usize,
    max_depth: usize,
) -> bool {
    use crate::syntax::Expr;
    let mut pending: Vec<_> = roots.iter().map(|id| (*id, 0usize)).collect();
    let mut work = 0usize;
    while let Some((id, depth)) = pending.pop() {
        if work >= max_work || depth > max_depth { return false; }
        work += 1;
        let Some(node) = expressions.get(id) else { return false; };
        match node {
            Expr::App { fun, arg } => { pending.push((*fun,depth+1)); pending.push((*arg,depth+1)); }
            Expr::Lam { domain, body } | Expr::Pi { domain, body } => { pending.push((*domain,depth+1)); pending.push((*body,depth+1)); }
            Expr::Let { ty, value, body } => { pending.push((*ty,depth+1)); pending.push((*value,depth+1)); pending.push((*body,depth+1)); }
            Expr::Proj { structure, .. } => pending.push((*structure,depth+1)),
            Expr::Const { levels, .. } if levels.len() > 4 => return false,
            Expr::NatLit(_) | Expr::StrLit(_) => return false,
            Expr::Const { .. } | Expr::Sort(_) | Expr::BVar(_) => {}
        }
    }
    true
}

#[cfg(test)]
mod probe_tests {
    use super::probe_expression_budget;
    use crate::{id::{ExprId, IdTable}, syntax::Expr};
    #[test]
    fn probe_work_counts_shared_occurrences_and_depth_separately() {
        let mut e=IdTable::default();
        e.insert(ExprId(0),Expr::BVar(0)).unwrap();
        e.insert(ExprId(1),Expr::App { fun:ExprId(0), arg:ExprId(0) }).unwrap();
        assert!(probe_expression_budget(&e,&[ExprId(1)],3,1));
        assert!(!probe_expression_budget(&e,&[ExprId(1)],2,1));
        assert!(!probe_expression_budget(&e,&[ExprId(1)],3,0));
        assert!(!probe_expression_budget(&e,&[ExprId(99)],3,1));
    }
}
