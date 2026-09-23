use std::fmt;
use std::hash::{Hash, Hasher};
use std::rc::Rc;
use std::sync::atomic::{AtomicU64, Ordering};

use crate::id::{ExprId, NameId};
use crate::level::LevelTerm;

static NEXT_ENV_FRAME_ID: AtomicU64 = AtomicU64::new(1);

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

#[derive(Clone, Debug)]
pub enum EnvBinding {
    Closure(Closure),
    Free(FreeId),
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

    fn extend_binding(&self, value: EnvBinding) -> Self {
        Self(Rc::new(EnvNode::Extend {
            id: NEXT_ENV_FRAME_ID.fetch_add(1, Ordering::Relaxed),
            parent: self.clone(),
            value,
        }))
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
    Sort(LevelTerm),
    Pi { domain: Closure, body: Closure },
    Lam { domain: Closure, body: Closure },
    Neutral(Neutral),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Neutral {
    pub head: NeutralHead,
    pub spine: Vec<Closure>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum NeutralHead {
    Free(FreeId),
    Const {
        name: NameId,
        levels: Vec<LevelTerm>,
    },
}
