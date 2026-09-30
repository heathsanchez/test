use std::fmt;
use std::hash::{Hash, Hasher};
use std::rc::Rc;
use std::sync::atomic::{AtomicU64, Ordering};

use crate::id::{ExprId, NameId};
use crate::level::LevelTerm;
use crate::nat::BigNat;

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
    term: ClosureTerm,
    pub env: EnvFrame,
    pub levels: LevelSubstitution,
}

// Runtime predecessors need not occur in the immutable export expression table.
// Keeping them distinct from ExprId prevents syntax shortcuts or memo keys from
// accidentally identifying a computed literal with an unrelated expression.
#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum ClosureTerm {
    Expression(ExprId),
    NatLiteral(BigNat),
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
            term: ClosureTerm::Expression(expr),
            env,
            levels: LevelSubstitution::default(),
        }
    }

    pub fn with_levels(expr: ExprId, env: EnvFrame, levels: LevelSubstitution) -> Self {
        Self {
            term: ClosureTerm::Expression(expr),
            env,
            levels,
        }
    }

    pub fn nat_literal(value: BigNat) -> Self {
        Self {
            term: ClosureTerm::NatLiteral(value),
            env: EnvFrame::empty(),
            levels: LevelSubstitution::default(),
        }
    }

    pub fn expression(&self) -> Option<ExprId> {
        match self.term {
            ClosureTerm::Expression(expr) => Some(expr),
            ClosureTerm::NatLiteral(_) => None,
        }
    }

    pub fn literal(&self) -> Option<&BigNat> {
        match &self.term {
            ClosureTerm::NatLiteral(value) => Some(value),
            ClosureTerm::Expression(_) => None,
        }
    }

    pub fn with_env(&self, env: EnvFrame) -> Self {
        Self {
            term: self.term.clone(),
            env,
            levels: self.levels.clone(),
        }
    }

    pub fn under_free(&self, free: FreeId) -> Self {
        self.with_env(self.env.extend_free(free))
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
    Projection {
        type_name: NameId,
        index: usize,
        structure: Box<Neutral>,
    },
}
