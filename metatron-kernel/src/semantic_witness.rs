//! Opt-in, partial observations of actual kernel environment lookups.
//!
//! This is not a complete read graph. TypeChecker also consults native
//! primitive flags, recursor/projection maps and source expression tables.
//! Consequently every observation carries the full export as a global barrier
//! and grants no authority to reuse a proof or skip any checker operation.

use std::cell::RefCell;
use std::collections::BTreeSet;

use crate::observation::CheckedDecl;
use crate::id::NameId;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct ConstantRead {
    pub name_id: u64,
    /// False is a real environment absence observation, not an omitted read.
    pub present: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObservedSemanticWitness {
    pub declaration: CheckedDecl,
    pub global_export_sha256: [u8; 32],
    pub constant_reads: Vec<ConstantRead>,
    pub read_coverage: &'static str,
    pub verification_reuse_authority: &'static str,
    pub proof_skips: u64,
}

thread_local! {
    static ACTIVE_READS: RefCell<Option<BTreeSet<ConstantRead>>> = const { RefCell::new(None) };
}

/// Restores the previous context on nested invocations or an early exit.
pub(crate) struct ReadScope {
    previous: Option<BTreeSet<ConstantRead>>,
}

impl ReadScope {
    pub(crate) fn enter() -> Self {
        let previous = ACTIVE_READS.with(|slot| slot.replace(Some(BTreeSet::new())));
        Self { previous }
    }

    /// A callback occurs only after ordinary Nucleus admission succeeds.
    pub(crate) fn drain(&self) -> Vec<ConstantRead> {
        ACTIVE_READS.with(|slot| {
            slot.borrow_mut()
                .as_mut()
                .map(std::mem::take)
                .unwrap_or_default()
                .into_iter()
                .collect()
        })
    }
}

impl Drop for ReadScope {
    fn drop(&mut self) {
        ACTIVE_READS.with(|slot| {
            slot.replace(self.previous.take());
        });
    }
}

pub(crate) fn record_constant_get(name: NameId, present: bool) {
    ACTIVE_READS.with(|slot| {
        if let Some(reads) = slot.borrow_mut().as_mut() {
            reads.insert(ConstantRead { name_id: name.0, present });
        }
    });
}

#[cfg(test)]
mod tests {
    use super::{ConstantRead, ReadScope};
    use crate::environment::Environment;
    use crate::id::NameId;

    #[test]
    fn absence_and_nested_scopes_keep_separate_read_sets() {
        let outer = ReadScope::enter();
        assert!(Environment::empty().get(NameId(77)).is_none());
        {
            let inner = ReadScope::enter();
            assert!(Environment::empty().get(NameId(88)).is_none());
            assert_eq!(inner.drain(), vec![ConstantRead {name_id: 88, present: false}]);
        }
        assert_eq!(outer.drain(), vec![ConstantRead {name_id: 77, present: false}]);
    }
}
