//! Deterministic, feature-gated operation counters.
//!
//! These counters are evidence instruments, never semantic inputs.  They are
//! thread-local so parallel tests and independent checker calls do not share
//! observation state.  Normal Arena builds omit this module and every update.

use std::cell::Cell;

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
}

pub(crate) fn causal_scope() {
    CAUSAL_SCOPE.set(CAUSAL_SCOPE.get().saturating_add(1));
    CAUSAL_EVENTS.set(0);
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
