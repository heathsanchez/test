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
    NatLit(BigNat),
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

    pub(crate) fn extend_nat_literal(&self, number: BigNat) -> Self {
        self.extend_binding(EnvBinding::NatLit(number))
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

    /// Borrow an immutable capture without recursively cloning its payload.
    pub(crate) fn lookup_binding_ref(&self, mut index: u64) -> Option<&EnvBinding> {
        let mut frame = self;
        loop {
            match frame.0.as_ref() {
                EnvNode::Empty => return None,
                EnvNode::Extend { value, .. } if index == 0 => return Some(value),
                EnvNode::Extend { parent, .. } => { index -= 1; frame = parent; }
            }
        }
    }

    /// Retrieve the *identity of the immutable binding node* read by one
    /// de Bruijn index, in addition to its value. Typed binder authority is
    /// attached to the node when a checked Pi/Lam/Let introduces it. The
    /// node ID is a key for that evidence, NOT an equality of local terms.
    pub(crate) fn lookup_with_node_id(&self, index: u64) -> Option<(u64, EnvBinding)> {
        let mut frame=self.clone();
        let mut index=index;
        loop {
            match frame.0.as_ref() {
                EnvNode::Empty => return None,
                EnvNode::Extend {id,parent,value} if index==0 =>
                    return Some((*id,value.clone())),
                EnvNode::Extend {parent,..} => {
                    index=index.checked_sub(1)?;
                    frame=parent.clone();
                }
            }
        }
    }

    /// Identify the immutable lexical binding without cloning its value.
    /// For diagnostics only: node identity is not semantic equality of terms.
    #[cfg(feature="diagnostics")]
    pub(crate) fn diagnostic_binding_node_id(&self, mut index: u64) -> Option<u64> {
        let mut frame=self;
        loop {
            match frame.0.as_ref() {
                EnvNode::Empty => return None,
                EnvNode::Extend {id,..} if index == 0 => return Some(*id),
                EnvNode::Extend {parent,..} => {index=index.checked_sub(1)?;frame=parent;}
            }
        }
    }

    /// C219 source-independent lexical-freshness certificate. Every source
    /// expression uses de Bruijn indices, never direct FreeIds. After
    /// separately establishing complete source support and enough lexical
    /// bindings, no captured FreeId equal to needle means no old binding
    /// can be captured by opening the fresh binder.
    ///
    /// Returns None on exhausted work, false on capture/missing bindings;
    /// neither result authorizes any reduction or new type judgment.
    pub(crate) fn certified_lexical_absence(
        &self, needle: FreeId, min_direct: u64, remaining: &mut usize,
    ) -> Option<bool> {
        enum Scan<'a> { Frame(&'a EnvFrame), Neutral(&'a Neutral) }
        let mut root = self;
        let mut direct = 0u64;
        while let EnvNode::Extend { parent, .. } = root.0.as_ref() {
            if *remaining == 0 { return None; }
            *remaining -= 1;
            direct = direct.checked_add(1)?;
            root = parent;
        }
        if direct < min_direct { return Some(false); }

        let mut visited = std::collections::HashSet::<u64>::new();
        let mut pending = vec![Scan::Frame(self)];
        while let Some(item) = pending.pop() {
            if *remaining == 0 { return None; }
            *remaining -= 1;
            match item {
                Scan::Frame(frame) => {
                    if !visited.insert(frame.id()) { continue; }
                    if let EnvNode::Extend { parent, value, .. } = frame.0.as_ref() {
                        pending.push(Scan::Frame(parent));
                        match value {
                            EnvBinding::Free(f) if *f == needle => return Some(false),
                            EnvBinding::Closure(c) => pending.push(Scan::Frame(&c.env)),
                            EnvBinding::Neutral(n) => pending.push(Scan::Neutral(n)),
                            EnvBinding::Free(_) | EnvBinding::NatLit(_) => {}
                        }
                    }
                }
                Scan::Neutral(n) => {
                    match &n.head {
                        NeutralHead::Free(f) if *f == needle => return Some(false),
                        NeutralHead::Projection { structure, .. } =>
                            pending.push(Scan::Neutral(structure.as_ref())),
                        NeutralHead::Const { .. } | NeutralHead::Free(_) => {}
                    }
                    for c in &n.spine { pending.push(Scan::Frame(&c.env)); }
                }
            }
        }
        Some(true)
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

    pub(crate) fn entries(&self) -> impl Iterator<Item=&(NameId,LevelTerm)> { self.0.iter() }
    /// Identity of this immutable substitution allocation. Callers using it
    /// as a witness must retain a clone to prevent address recycling.
    pub(crate) fn identity(&self)->usize {Rc::as_ptr(&self.0) as usize}

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
                    EnvBinding::NatLit(n) => Some((EnvBinding::NatLit(n.clone()), false)),
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
                        // FreeId is the lexical level at which this binder
                        // was opened. Once the exact binder cell is found,
                        // its parent is outside this binder's scope. Reuse
                        // the parent without descending through thousands
                        // of unrelated outer frames.
                        if matches!(value, EnvBinding::Free(free) if *free == self.source)
                            || matches!(value, EnvBinding::Neutral(Neutral {
                                head: NeutralHead::Free(free), spine,
                            }) if *free == self.source && spine.is_empty())
                        {
                            (parent.extend_binding(
                                EnvBinding::Closure(self.actual.clone())
                            ), true)
                        } else {
                            let (parent_new, parent_changed) = self.frame(parent)?;
                            let (value_new, value_changed) = self.binding(value)?;
                            if parent_changed || value_changed {
                                (parent_new.extend_binding(value_new), true)
                            } else {
                                (f.clone(), false)
                            }
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


#[cfg(test)]
mod c219_lexical_freshness_tests {
    use super::*;

    #[test]
    fn requires_full_lexical_witness_and_sufficient_binding_depth() {
        let empty = EnvFrame::empty();
        let mut steps = 32;
        assert_eq!(empty.certified_lexical_absence(FreeId(2), 0, &mut steps), Some(true));
        let outer = empty.extend_free(FreeId(1));
        let mut steps = 32;
        assert_eq!(outer.certified_lexical_absence(FreeId(2), 1, &mut steps), Some(true));
        let mut steps = 32;
        assert_eq!(outer.certified_lexical_absence(FreeId(1), 1, &mut steps), Some(false));
        let mut steps = 32;
        assert_eq!(outer.certified_lexical_absence(FreeId(2), 2, &mut steps), Some(false));
        let mut steps = 0;
        assert_eq!(outer.certified_lexical_absence(FreeId(2), 1, &mut steps), None);
    }

    #[test]
    fn follows_nested_captured_closures_and_neutral_spines() {
        let empty = EnvFrame::empty();
        let inner = empty.extend_free(FreeId(7));
        let captured = empty.extend(Closure::new(ExprId(1), inner.clone()));
        let mut steps = 64;
        assert_eq!(captured.certified_lexical_absence(FreeId(7), 0, &mut steps), Some(false));
        let neutral = Neutral {
            head: NeutralHead::Projection {
                type_name: NameId(1), index: 0,
                structure: Box::new(Neutral {
                    head: NeutralHead::Free(FreeId(9)), spine: vec![]
                }),
            },
            spine: vec![Closure::new(ExprId(2), inner)],
        };
        let nested = empty.extend_neutral(neutral);
        let mut steps = 64;
        assert_eq!(nested.certified_lexical_absence(FreeId(7), 1, &mut steps), Some(false));
        let mut steps = 64;
        assert_eq!(nested.certified_lexical_absence(FreeId(9), 1, &mut steps), Some(false));
        let mut steps = 64;
        assert_eq!(nested.certified_lexical_absence(FreeId(10), 1, &mut steps), Some(true));
    }
}
