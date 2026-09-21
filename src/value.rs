use std::fmt;
use std::rc::Rc;
use std::sync::atomic::{AtomicU64, Ordering};

use crate::id::{ExprId, LevelId, NameId};

static NEXT_ENV_FRAME_ID: AtomicU64 = AtomicU64::new(1);

#[derive(Clone)]
pub struct EnvFrame(Rc<EnvNode>);

#[derive(Clone, Debug)]
enum EnvNode {
    Empty,
    Extend {
        id: u64,
        parent: EnvFrame,
        value: Closure,
    },
}

impl EnvFrame {
    pub fn empty() -> Self {
        Self(Rc::new(EnvNode::Empty))
    }

    pub fn extend(&self, value: Closure) -> Self {
        Self(Rc::new(EnvNode::Extend {
            id: NEXT_ENV_FRAME_ID.fetch_add(1, Ordering::Relaxed),
            parent: self.clone(),
            value,
        }))
    }

    pub fn lookup(&self, index: u64) -> Option<Closure> {
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

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Closure {
    pub expr: ExprId,
    pub env: EnvFrame,
}

impl Closure {
    pub fn new(expr: ExprId, env: EnvFrame) -> Self {
        Self { expr, env }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Value {
    Sort(LevelId),
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
    Free(u64),
    Const { name: NameId, levels: Vec<LevelId> },
}
