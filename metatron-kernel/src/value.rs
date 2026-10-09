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


/// Substitute a checked argument for one lexical FreeId captured by type
/// inference. This only rewrites immutable environment bindings: expression
/// syntax, universe substitutions, and all other local names are preserved.
/// Unsupported neutral applications refuse substitution rather than assuming
/// any equality.
impl Closure {
    pub(crate) fn substitute_local_free(
        &self,
        source: FreeId,
        actual: &Closure,
        remaining: &mut usize,
    ) -> Option<Self> {
        struct Subst<'a> {
            source: FreeId,
            actual: &'a Closure,
            remaining: &'a mut usize,
            frames: std::collections::HashMap<u64, (EnvFrame, bool)>,
        }
        impl Subst<'_> {
            fn tick(&mut self) -> Option<()> {
                if *self.remaining == 0 {
                    return None;
                }
                *self.remaining -= 1;
                Some(())
            }
            fn closure(&mut self, c: &Closure) -> Option<(Closure, bool)> {
                self.tick()?;
                let (env, changed) = self.frame(&c.env)?;
                Some((
                    if changed {
                        Closure::with_levels(c.expr, env, c.levels.clone())
                    } else {
                        c.clone()
                    },
                    changed,
                ))
            }
            fn neutral(&mut self, n: &Neutral) -> Option<(Neutral, bool)> {
                self.tick()?;
                let (head, head_changed) = match &n.head {
                    NeutralHead::Free(f) if *f == self.source => {
                        // A neutral head applied to arguments cannot be
                        // replaced by an arbitrary syntax closure here.
                        return None;
                    }
                    NeutralHead::Free(f) => (NeutralHead::Free(*f), false),
                    NeutralHead::Const { name, levels } => (
                        NeutralHead::Const { name: *name, levels: levels.clone() },
                        false,
                    ),
                    NeutralHead::Projection { type_name, index, structure } => {
                        let (structure, changed) = self.neutral(structure)?;
                        (NeutralHead::Projection {
                            type_name: *type_name,
                            index: *index,
                            structure: Box::new(structure),
                        }, changed)
                    }
                };
                let mut changed = head_changed;
                let mut spine = Vec::with_capacity(n.spine.len());
                for c in &n.spine {
                    let (c, did_change) = self.closure(c)?;
                    changed |= did_change;
                    spine.push(c);
                }
                Some((
                    if changed { Neutral { head, spine } } else { n.clone() },
                    changed,
                ))
            }
            fn binding(&mut self, b: &EnvBinding) -> Option<(EnvBinding, bool)> {
                self.tick()?;
                match b {
                    EnvBinding::Free(f) if *f == self.source =>
                        Some((EnvBinding::Closure(self.actual.clone()), true)),
                    EnvBinding::Free(f) => Some((EnvBinding::Free(*f), false)),
                    EnvBinding::Closure(c) => {
                        let (c, changed) = self.closure(c)?;
                        Some((EnvBinding::Closure(c), changed))
                    }
                    EnvBinding::Neutral(n) => {
                        if let NeutralHead::Free(f) = n.head {
                            if f == self.source {
                                if n.spine.is_empty() {
                                    return Some((
                                        EnvBinding::Closure(self.actual.clone()),
                                        true,
                                    ));
                                }
                                return None;
                            }
                        }
                        let (n, changed) = self.neutral(n)?;
                        Some((EnvBinding::Neutral(n), changed))
                    }
                }
            }
            fn frame(&mut self, f: &EnvFrame) -> Option<(EnvFrame, bool)> {
                self.tick()?;
                if let Some(found) = self.frames.get(&f.id()) {
                    return Some(found.clone());
                }
                let result = match f.0.as_ref() {
                    EnvNode::Empty => (f.clone(), false),
                    EnvNode::Extend { parent, value, .. } => {
                        let (parent_new, parent_changed) = self.frame(parent)?;
                        let (value_new, value_changed) = self.binding(value)?;
                        if parent_changed || value_changed {
                            (parent_new.extend_binding(value_new), true)
                        } else {
                            (f.clone(), false)
                        }
                    }
                };
                self.frames.insert(f.id(), result.clone());
                Some(result)
            }
        }

        let mut s = Subst {
            source, actual, remaining,
            frames: std::collections::HashMap::new(),
        };
        s.closure(self).map(|(c, _)| c)
    }
}
