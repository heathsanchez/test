use std::cell::RefCell;
use std::collections::HashMap;
use std::fmt;
use std::hash::{Hash, Hasher};
use std::rc::{Rc, Weak};
use std::sync::atomic::{AtomicU64, Ordering};

use crate::id::{ExprId, NameId};
use crate::level::LevelTerm;
use crate::nat::BigNat;

static NEXT_ENV_FRAME_ID: AtomicU64 = AtomicU64::new(1);

// Scoped by a nonempty parent frame. Empty roots deliberately do not intern:
// ExprIds and FreeIds alone are not globally meaningful across distinct
// proof exports or independently constructed lexical scopes.
thread_local! {
    static ENV_FRAME_INTERN: RefCell<HashMap<(u64, EnvBinding), Weak<EnvNode>>> =
        RefCell::new(HashMap::new());
}

#[derive(Clone)]
pub struct EnvFrame(Rc<EnvNode>);

#[derive(Clone, Debug)]
enum EnvNode {
    Empty,
    Extend {
        id: u64,
        parent: EnvFrame,
        value: EnvBinding,
    },
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum EnvBinding {
    Closure(Closure),
    Free(FreeId),
    Neutral(Neutral),
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct FreeId(pub u64);

impl EnvFrame {
    pub fn empty() -> Self {
        Self(Rc::new(EnvNode::Empty))
    }

    pub fn extend(&self, value: Closure) -> Self {
        self.extend_binding(EnvBinding::Closure(value))
    }

    pub fn extend_free(&self, free: FreeId) -> Self {
        self.extend_binding(EnvBinding::Free(free))
    }

    pub fn extend_neutral(&self, neutral: Neutral) -> Self {
        self.extend_binding(EnvBinding::Neutral(neutral))
    }

    fn extend_binding(&self, value: EnvBinding) -> Self {
        let key = (self.id(), value.clone());
        // A globally shared Empty frame has id=0. Interning its children
        // could alias different exports with independent expression tables.
        if key.0 != 0 {
            if let Some(existing) = ENV_FRAME_INTERN.with(|table| {
                table.borrow().get(&key).and_then(Weak::upgrade)
            }) {
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_ENV_INTERN").is_some() {
                    eprintln!("NUCLEUS_ENV_INTERN:hit:parent={}", key.0);
                }
                return Self(existing);
            }
        }
        let frame = Self(Rc::new(EnvNode::Extend {
            id: NEXT_ENV_FRAME_ID.fetch_add(1, Ordering::Relaxed),
            parent: self.clone(),
            value,
        }));
        if key.0 != 0 {
            ENV_FRAME_INTERN.with(|table| {
                let mut table = table.borrow_mut();
                // Weak entries own no frame memory. Bounded eviction may
                // lose sharing but cannot change any semantic judgment.
                if table.len() >= 16384 {
                    table.clear();
                }
                table.insert(key, Rc::downgrade(&frame.0));
            });
        }
        frame
    }

    pub fn lookup(&self, index: u64) -> Option<EnvBinding> {
        let mut frame = self.clone();
        let mut remaining = index;
        loop {
            match frame.0.as_ref() {
                EnvNode::Empty => return None,
                EnvNode::Extend { parent, value, .. } if remaining == 0 => {
                    return Some(value.clone());
                }
                EnvNode::Extend { parent, .. } => {
                    remaining -= 1;
                    frame = parent.clone();
                }
            }
        }
    }

    pub fn id(&self) -> u64 {
        match self.0.as_ref() {
            EnvNode::Empty => 0,
            EnvNode::Extend { id, .. } => *id,
        }
    }
}

impl Default for EnvFrame {
    fn default() -> Self {
        Self::empty()
    }
}

impl fmt::Debug for EnvFrame {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EnvFrame")
            .field("id", &self.id())
            .finish_non_exhaustive()
    }
}

impl PartialEq for EnvFrame {
    fn eq(&self, other: &Self) -> bool {
        self.id() == other.id()
    }
}

impl Eq for EnvFrame {}

impl Hash for EnvFrame {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id().hash(state);
    }
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct Closure {
    pub expr: ExprId,
    pub env: EnvFrame,
    pub levels: LevelSubstitution,
}

#[derive(Clone, Debug, Default, Eq, Hash, PartialEq)]
pub struct LevelSubstitution(Rc<Vec<(NameId, LevelTerm)>>);

impl LevelSubstitution {
    pub fn new(entries: Vec<(NameId, LevelTerm)>) -> Self {
        Self(Rc::new(entries))
    }

    pub fn to_map(&self) -> std::collections::HashMap<NameId, LevelTerm> {
        self.0.iter().cloned().collect()
    }
}

impl crate::level::LevelSubstitutionLookup for LevelSubstitution {
    #[inline]
    fn lookup_level(&self, name: NameId) -> Option<LevelTerm> {
        self.0
            .iter()
            .find_map(|(candidate, level)| (*candidate == name).then(|| level.clone()))
    }
}

impl Closure {
    pub fn new(expr: ExprId, env: EnvFrame) -> Self {
        Self {
            expr,
            env,
            levels: LevelSubstitution::default(),
        }
    }

    pub fn with_levels(expr: ExprId, env: EnvFrame, levels: LevelSubstitution) -> Self {
        Self { expr, env, levels }
    }

    pub fn under_free(&self, free: FreeId) -> Self {
        Self::with_levels(self.expr, self.env.extend_free(free), self.levels.clone())
    }

    pub fn sibling(&self, expr: ExprId, env: EnvFrame) -> Self {
        Self::with_levels(expr, env, self.levels.clone())
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Value {
    NatLit(BigNat),
    Sort(LevelTerm),
    Pi { domain: Closure, body: Closure },
    Lam { domain: Closure, body: Closure },
    Neutral(Neutral),
    StuckProjection {
        type_name: NameId,
        index: usize,
        structure: Closure,
        spine: Vec<Closure>,
    },
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub struct Neutral {
    pub head: NeutralHead,
    pub spine: Vec<Closure>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum NeutralHead {
    Free(FreeId),
    Const {
        name: NameId,
        levels: Vec<LevelTerm>,
    },
    Projection {
        type_name: NameId,
        index: usize,
        structure: Box<Neutral>,
    },
}

#[cfg(test)]
mod interned_environment_tests {
    use super::*;

    #[test]
    fn sibling_frames_share_only_identical_substitutions() {
        let root = EnvFrame::empty();
        let parent = root.extend_free(FreeId(91));
        let a = parent.extend_free(FreeId(23));
        let b = parent.extend_free(FreeId(23));
        let c = parent.extend_free(FreeId(24));
        assert_eq!(a.id(), b.id(), "identical parent and binding must share");
        assert_ne!(a.id(), c.id(), "distinct substitutions must remain distinct");
        assert_eq!(a.lookup(1).is_some(), true);
    }

    #[test]
    fn independent_empty_roots_never_alias_by_interning() {
        let a = EnvFrame::empty().extend_free(FreeId(7));
        let b = EnvFrame::empty().extend_free(FreeId(7));
        assert_ne!(a.id(), b.id());
    }
}
