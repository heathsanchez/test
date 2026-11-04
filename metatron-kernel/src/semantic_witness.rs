//! Opt-in, partial kernel read traces. Whole-export SHA-256 remains mandatory.
//! No observed lookup can approve proof reuse or bypass Nucleus checking.

use std::cell::RefCell;
use std::collections::BTreeSet;

use crate::id::NameId;
use crate::observation::CheckedDecl;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct ConstantRead {
    pub name_id: u64,
    pub present: bool,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct TableRead {
    pub table: &'static str,
    pub access: &'static str,
    pub id: Option<u64>,
    pub present: Option<bool>,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct EnvironmentRead {
    pub channel: &'static str,
    pub name_id: Option<u64>,
    pub present: Option<bool>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct GlobalGuard {
    pub stage: &'static str,
    pub result: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlobalTrace {
    pub source_resolution_reads: Vec<TableRead>,
    pub preflight_reads: Vec<TableRead>,
    pub guards: Vec<GlobalGuard>,
    pub read_coverage: &'static str,
    pub verification_reuse_authority: &'static str,
    pub proof_skips: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObservedSemanticWitness {
    pub declaration: CheckedDecl,
    pub global_export_sha256: [u8; 32],
    pub constant_reads: Vec<ConstantRead>,
    pub table_reads: Vec<TableRead>,
    pub environment_reads: Vec<EnvironmentRead>,
    pub read_coverage: &'static str,
    pub verification_reuse_authority: &'static str,
    pub proof_skips: u64,
}

#[derive(Clone, Copy, Default)]
enum TracePhase {
    #[default]
    SourceResolution,
    GlobalPreflight,
    Declaration,
}

#[derive(Default)]
struct TraceState {
    phase: TracePhase,
    constants: BTreeSet<ConstantRead>,
    tables: BTreeSet<TableRead>,
    environment: BTreeSet<EnvironmentRead>,
    source_resolution: BTreeSet<TableRead>,
    preflight: BTreeSet<TableRead>,
    guards: Vec<GlobalGuard>,
}

thread_local! {
    static ACTIVE_TRACE: RefCell<Option<TraceState>> = const { RefCell::new(None) };
}

pub(crate) struct ReadBundle {
    pub(crate) constants: Vec<ConstantRead>,
    pub(crate) tables: Vec<TableRead>,
    pub(crate) environment: Vec<EnvironmentRead>,
}

/// Restores the previous state and phase even on an early exit.
pub(crate) struct ReadScope {
    previous: Option<TraceState>,
}

impl ReadScope {
    pub(crate) fn enter() -> Self {
        let previous = ACTIVE_TRACE.with(|slot| slot.replace(Some(TraceState::default())));
        Self { previous }
    }

    pub(crate) fn drain_bundle(&self) -> ReadBundle {
        ACTIVE_TRACE.with(|slot| {
            let mut slot = slot.borrow_mut();
            let active = slot.as_mut().expect("active semantic read scope");
            ReadBundle {
                constants: std::mem::take(&mut active.constants).into_iter().collect(),
                tables: std::mem::take(&mut active.tables).into_iter().collect(),
                environment: std::mem::take(&mut active.environment).into_iter().collect(),
            }
        })
    }

    #[cfg(test)]
    pub(crate) fn drain(&self) -> Vec<ConstantRead> {
        self.drain_bundle().constants
    }

    pub(crate) fn global_trace(&self) -> GlobalTrace {
        ACTIVE_TRACE.with(|slot| {
            let slot = slot.borrow();
            let active = slot.as_ref().expect("active semantic read scope");
            GlobalTrace {
                source_resolution_reads: active.source_resolution.iter().copied().collect(),
                preflight_reads: active.preflight.iter().copied().collect(),
                guards: active.guards.clone(),
                read_coverage: "PARTIAL",
                verification_reuse_authority: "NONE",
                proof_skips: 0,
            }
        })
    }
}

impl Drop for ReadScope {
    fn drop(&mut self) {
        ACTIVE_TRACE.with(|slot| {
            slot.replace(self.previous.take());
        });
    }
}

pub(crate) fn phase_preflight() {
    ACTIVE_TRACE.with(|slot| {
        if let Some(active) = slot.borrow_mut().as_mut() {
            active.phase = TracePhase::GlobalPreflight;
        }
    });
}

pub(crate) fn phase_declarations() {
    ACTIVE_TRACE.with(|slot| {
        if let Some(active) = slot.borrow_mut().as_mut() {
            active.phase = TracePhase::Declaration;
        }
    });
}

pub(crate) fn record_global_guard(stage: &'static str, result: &'static str) {
    ACTIVE_TRACE.with(|slot| {
        if let Some(active) = slot.borrow_mut().as_mut() {
            active.guards.push(GlobalGuard { stage, result });
        }
    });
}

pub(crate) fn record_table_access(
    table: &'static str, access: &'static str, id: Option<u64>, present: Option<bool>,
) {
    ACTIVE_TRACE.with(|slot| {
        if let Some(active) = slot.borrow_mut().as_mut() {
            let read = TableRead { table, access, id, present };
            match active.phase {
                TracePhase::SourceResolution => { active.source_resolution.insert(read); }
                TracePhase::GlobalPreflight => { active.preflight.insert(read); }
                TracePhase::Declaration => { active.tables.insert(read); }
            }
        }
    });
}

pub(crate) fn record_constant_get(name: NameId, present: bool) {
    ACTIVE_TRACE.with(|slot| {
        if let Some(active) = slot.borrow_mut().as_mut() {
            active.constants.insert(ConstantRead { name_id: name.0, present });
            active.environment.insert(EnvironmentRead {
                channel: "constant", name_id: Some(name.0), present: Some(present),
            });
        }
    });
}

pub(crate) fn record_environment_access(
    channel: &'static str, name_id: Option<NameId>, present: Option<bool>,
) {
    ACTIVE_TRACE.with(|slot| {
        if let Some(active) = slot.borrow_mut().as_mut() {
            active.environment.insert(EnvironmentRead {
                channel, name_id: name_id.map(|id| id.0), present,
            });
        }
    });
}

#[cfg(test)]
mod tests {
    use super::{ConstantRead, ReadScope, TableRead, record_table_access, phase_preflight};
    use crate::environment::Environment;
    use crate::id::NameId;

    #[test]
    fn absence_and_nested_scopes_keep_separate_read_sets() {
        let outer = ReadScope::enter();
        assert!(Environment::empty().get(NameId(77)).is_none());
        phase_preflight();
        record_table_access("expression", "point", Some(3), Some(true));
        {
            let inner = ReadScope::enter();
            assert!(Environment::empty().get(NameId(88)).is_none());
            assert_eq!(inner.drain(), vec![ConstantRead { name_id: 88, present: false }]);
        }
        assert_eq!(outer.drain(), vec![ConstantRead { name_id: 77, present: false }]);
        assert_eq!(outer.global_trace().preflight_reads,
            vec![TableRead { table: "expression", access: "point", id: Some(3), present: Some(true) }]);
    }
}
