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
