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
        // Exact immutable ancestors at distances 1, 2, 4, ... .
        // These retain physical nodes; they do not create binder identities.
        ancestors: Vec<EnvFrame>,
        evaluated_origin: Option<(crate::machine::AuthorityId,Closure)>,
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
    pub(crate) fn parent_frame(&self)->Option<Self>{match self.0.as_ref(){EnvNode::Extend{parent,..}=>Some(parent.clone()),EnvNode::Empty=>None}}

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

    fn extend_binding(&self,value:EnvBinding)->Self {
        self.extend_binding_with_allowance(value,None).expect("unbounded structural frame construction")
    }

    pub(crate) fn extend_free_paid(&self,free:FreeId,remaining:&mut usize)->Option<Self> {
        self.extend_binding_with_allowance(EnvBinding::Free(free),Some(remaining))
    }

    pub(crate) fn extend_neutral_paid(&self,neutral:Neutral,remaining:&mut usize)->Option<Self> {
        self.extend_binding_with_allowance(EnvBinding::Neutral(neutral),Some(remaining))
    }

    pub(crate) fn extend_evaluated(&self,authority:crate::machine::AuthorityId,binder:Closure,argument:Closure)->Self {
        debug_assert_eq!(binder.env,*self);
        self.extend_binding_recorded(EnvBinding::Closure(argument),Some((authority,binder)),None).expect("unbounded source evaluator binding")
    }
    pub(crate) fn evaluated_binding_origin(&self)->Option<(crate::machine::AuthorityId,Closure)>{
        match self.0.as_ref(){EnvNode::Extend{evaluated_origin,..}=>evaluated_origin.clone(),EnvNode::Empty=>None}
    }
    fn extend_binding_with_allowance(&self,value:EnvBinding,allowance:Option<&mut usize>)->Option<Self>{self.extend_binding_recorded(value,None,allowance)}
    fn extend_binding_recorded(&self,value:EnvBinding,evaluated_origin:Option<(crate::machine::AuthorityId,Closure)>,mut allowance:Option<&mut usize>)->Option<Self> {
        fn charge(allowance:&mut Option<&mut usize>)->bool {
            if let Some(remaining)=allowance.as_deref_mut(){if *remaining==0{return false;}*remaining-=1;}
            true
        }
        if !charge(&mut allowance){return None;}
        let mut ancestors=vec![self.clone()];
        let mut level=0;
        loop {
            if !charge(&mut allowance){return None;}
            let next=match ancestors[level].0.as_ref() {
                EnvNode::Extend{ancestors:prior,..}=>prior.get(level).cloned(),
                EnvNode::Empty=>None,
            };
            let Some(next)=next else{break;};
            ancestors.push(next);level+=1;
        }
        Some(Self(Rc::new(EnvNode::Extend {
            id: NEXT_ENV_FRAME_ID.fetch_add(1, Ordering::Relaxed),
            parent: self.clone(),
            value,
            ancestors,
            evaluated_origin,
        })))
    }

    pub(crate) fn parent_id(&self)->Option<u64>{
        match self.0.as_ref(){EnvNode::Extend{parent,..}=>Some(parent.id()),EnvNode::Empty=>None}
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

    /// Retain the exact immutable node which owns one captured binding.
    pub(crate) fn binding_frame(&self,mut index:u64)->Option<EnvFrame> {
        let mut frame=self.clone();
        while index!=0 {
            let level=index.ilog2() as usize;
            let next=match frame.0.as_ref() {
                EnvNode::Extend{ancestors,..}=>ancestors.get(level)?.clone(),
                EnvNode::Empty=>return None,
            };
            frame=next;index-=1u64<<level;
        }
        match frame.0.as_ref(){EnvNode::Extend{..}=>Some(frame),EnvNode::Empty=>None}
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
                EnvNode::Extend {id,parent,value,..} if index==0 =>
                    return Some((*id,value.clone())),
                EnvNode::Extend {parent,..} => {
                    index=index.checked_sub(1)?;
                    frame=parent.clone();
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
    Free(FreeId, Option<EnvFrame>),
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
        // Direct callers lack an AST support certificate. Conservatively
        // require one original target throughout the captured environment.
        let mut frames=vec![self.env.clone()];let mut neutrals=Vec::new();
        let mut seen=std::collections::HashSet::new();let mut target:Option<EnvFrame>=None;
        while !frames.is_empty()||!neutrals.is_empty() {
            if *remaining==0{return None;}*remaining-=1;
            if let Some(neutral)=neutrals.pop() {
                let neutral:Neutral=neutral;
                match neutral.head {
                    NeutralHead::Free(free,owner) if free==source=>{
                        let owner=owner?;
                        if !matches!(owner.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if *actual==source){return None;}
                        if target.as_ref().is_some_and(|t|t!=&owner){return None;}target=Some(owner);
                    },
                    NeutralHead::Projection{structure,..}=>neutrals.push(*structure),
                    _=>{},
                }
                frames.extend(neutral.spine.into_iter().map(|c|c.env));continue;
            }
            let frame=frames.pop()?;if !seen.insert(frame.id()){continue;}
            if let EnvNode::Extend{parent,value,..}=frame.0.as_ref(){
                frames.push(parent.clone());
                match value {
                    EnvBinding::Free(free) if *free==source=>{
                        if target.as_ref().is_some_and(|t|t!=&frame){return None;}target=Some(frame.clone());
                    },
                    EnvBinding::Closure(c)=>frames.push(c.env.clone()),
                    EnvBinding::Neutral(n)=>neutrals.push(n.clone()),
                    _=>{},
                }
            }
        }
        let Some(target)=target else{return Some(self.clone());};
        self.substitute_local_free_from_owner(source,&target,actual,remaining)
    }

    pub(crate) fn substitute_local_free_from_owner(
        &self, source:FreeId, source_owner:&EnvFrame, actual:&Closure, remaining:&mut usize,
    )->Option<Self> {
        if !matches!(source_owner.lookup_binding_ref(0),Some(EnvBinding::Free(free)) if *free==source){return None;}
        struct Subst<'a> {
            source: FreeId,
            source_owner:&'a EnvFrame,
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
                    NeutralHead::Free(f, Some(owner)) if *f == self.source && owner==self.source_owner => {
                        // A neutral head applied to arguments cannot be
                        // replaced by an arbitrary syntax closure here.
                        return None;
                    }
                    NeutralHead::Free(_, _) => (n.head.clone(), false),
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
            fn binding(&mut self, b: &EnvBinding, owner:&EnvFrame) -> Option<(EnvBinding, bool)> {
                self.tick()?;
                match b {
                    EnvBinding::Free(f) if *f == self.source && owner==self.source_owner =>
                        Some((EnvBinding::Closure(self.actual.clone()), true)),
                    EnvBinding::Free(f) => Some((EnvBinding::Free(*f), false)),
                    EnvBinding::NatLit(n) => Some((EnvBinding::NatLit(n.clone()), false)),
                    EnvBinding::Closure(c) => {
                        let (c, changed) = self.closure(c)?;
                        Some((EnvBinding::Closure(c), changed))
                    }
                    EnvBinding::Neutral(n) => {
                        if let NeutralHead::Free(f, Some(owner)) = &n.head {
                            if *f == self.source && owner==self.source_owner {
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
                        if matches!(value, EnvBinding::Free(free) if *free == self.source && f==self.source_owner)
                            || matches!(value, EnvBinding::Neutral(Neutral {
                                head: NeutralHead::Free(free, Some(owner)), spine,
                            }) if *free == self.source && owner==self.source_owner && spine.is_empty())
                        {
                            (parent.extend_binding(
                                EnvBinding::Closure(self.actual.clone())
                            ), true)
                        } else {
                            let (parent_new, parent_changed) = self.frame(parent)?;
                            let (mut value_new, value_changed) = self.binding(value,f)?;
                            if parent_changed && !value_changed {
                                if let EnvBinding::Free(free)=value {
                                    // This rebuilt cell still denotes the ORIGINAL
                                    // variable; allocation of its wrapper is no intro.
                                    value_new=EnvBinding::Neutral(Neutral {
                                        head:NeutralHead::Free(*free,Some(f.clone())),spine:vec![],
                                    });
                                }
                            }
                            if parent_changed || value_changed {
                                let origin=match f.evaluated_binding_origin(){Some((authority,binder))=>Some((authority,self.closure(&binder)?.0)),None=>None};
                                (parent_new.extend_binding_recorded(value_new,origin,None)?, true)
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
            source, source_owner, actual, remaining,
            frames: std::collections::HashMap::new(),
        };
        s.closure(self).map(|(c, _)| c)
    }
}

impl NeutralHead {
    /// Exact owner identity is structural. Typed alpha introduction is a
    /// separate checked-scope rule; numeric Free IDs confer no such authority.
    pub fn same_owned_free(&self, other: &Self) -> bool {
        matches!((self, other),
            (Self::Free(a, Some(x)), Self::Free(b, Some(y))) if a==b && x==y
                && matches!(x.lookup_binding_ref(0),Some(EnvBinding::Free(actual)) if actual==a))
    }
}

#[cfg(test)]
mod owned_neutral_substitution_tests {
    use super::*;
    #[test]
    fn rebuilding_a_surviving_free_retains_original_capture_owner() {
        let root=EnvFrame::empty().extend_free(FreeId(0));
        let survivor=root.extend_free(FreeId(7));
        let term=Closure::new(ExprId(0),survivor.clone());
        let actual=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(9)));
        let changed=term.substitute_local_free(FreeId(0),&actual,&mut 128).unwrap();
        assert_ne!(changed.env.id(),survivor.id());
        assert!(matches!(changed.env.lookup(0),Some(EnvBinding::Neutral(Neutral{
            head:NeutralHead::Free(FreeId(7),Some(owner)),spine})) if owner==survivor&&spine.is_empty()),
            "rebuilt alias must carry the original surviving Free owner");
        let replacement=Closure::new(ExprId(0),root).substitute_local_free(FreeId(0),&actual,&mut 32).unwrap();
        assert!(matches!(replacement.env.lookup(0),Some(EnvBinding::Closure(stored)) if stored==actual),
            "substituted value keeps its own actual source and origin");
    }
    #[test]
    fn substitution_declines_mixed_same_number_original_owners() {
        let first=EnvFrame::empty().extend_free(FreeId(0));
        let second=first.extend_free(FreeId(0));
        let actual=Closure::new(ExprId(0),EnvFrame::empty().extend_free(FreeId(9)));
        assert!(Closure::new(ExprId(0),second).substitute_local_free(FreeId(0),&actual,&mut 64).is_none(),
            "numeric target coincidence cannot choose one of unrelated original owners");
    }

}

/// One owner-sensitive substitution shared across an entire derived TYPE.
/// Explicit rebindings are checked introductions supplied by the typechecker.
pub(crate) struct OwnedTypeSubstitution {
 frames:std::collections::HashMap<u64,EnvFrame>,
 pub(crate) observed:Vec<EnvFrame>,
}
impl OwnedTypeSubstitution {
 pub(crate) fn new(original:&EnvFrame,actual:&Closure,remaining:&mut usize)->Option<(Self,EnvFrame)>{
  let parent=original.parent_frame()?;
  if *remaining==0{return None;}*remaining-=1;
  let replacement=parent.extend_binding_with_allowance(EnvBinding::Closure(actual.clone()),Some(remaining))?;
  let mut frames=std::collections::HashMap::new();frames.insert(original.id(),replacement.clone());
  Some((Self{frames,observed:vec![original.clone(),parent.clone()]},replacement))
 }
 pub(crate) fn bind(&mut self,old:&EnvFrame,new:EnvFrame)->Option<()>{
  if self.frames.contains_key(&old.id()){return None;}
  self.observed.push(old.clone());self.frames.insert(old.id(),new);Some(())
 }
 pub(crate) fn closure(&mut self,c:&Closure,remaining:&mut usize)->Option<Closure>{
  if *remaining==0{return None;}*remaining-=1;
  Some(Closure::with_levels(c.expr,self.frame(&c.env,remaining)?,c.levels.clone()))
 }
 fn neutral(&mut self,n:&Neutral,remaining:&mut usize)->Option<Neutral>{
  if *remaining==0{return None;}*remaining-=1;
  let head=match &n.head {
   NeutralHead::Free(f,Some(owner))=>{
    self.observed.push(owner.clone());
    if let Some(new)=self.frames.get(&owner.id()){
     match new.lookup_binding_ref(0){Some(EnvBinding::Free(new_free))=>NeutralHead::Free(*new_free,Some(new.clone())),_=>return None}
    }else{NeutralHead::Free(*f,Some(owner.clone()))}
   },
   NeutralHead::Free(_,None)=>return None,
   NeutralHead::Const{..}=>n.head.clone(),
   NeutralHead::Projection{type_name,index,structure}=>NeutralHead::Projection{type_name:*type_name,index:*index,structure:Box::new(self.neutral(structure,remaining)?)},
  };
  let mut spine=Vec::new();for c in &n.spine{spine.push(self.closure(c,remaining)?);}
  Some(Neutral{head,spine})
 }
 pub(crate) fn frame(&mut self,f:&EnvFrame,remaining:&mut usize)->Option<EnvFrame>{
  if *remaining==0{return None;}*remaining-=1;
  if let Some(new)=self.frames.get(&f.id()){return Some(new.clone());}
  self.observed.push(f.clone());
  let result=match f.0.as_ref(){
   EnvNode::Empty=>f.clone(),
   EnvNode::Extend{parent,value,..}=>{
    let new_parent=self.frame(parent,remaining)?;
    let binding=match value {
     EnvBinding::Free(free) if new_parent!=*parent=>EnvBinding::Neutral(Neutral{head:NeutralHead::Free(*free,Some(f.clone())),spine:vec![]}),
     EnvBinding::Free(free)=>EnvBinding::Free(*free),
     EnvBinding::Closure(c)=>EnvBinding::Closure(self.closure(c,remaining)?),
     EnvBinding::NatLit(n)=>EnvBinding::NatLit(n.clone()),
     EnvBinding::Neutral(n)=>{
      if n.spine.is_empty() && let NeutralHead::Free(_,Some(owner))=&n.head
       && let Some(new)=self.frames.get(&owner.id())
       && let Some(EnvBinding::Closure(actual))=new.lookup_binding_ref(0){EnvBinding::Closure(actual.clone())}
      else{EnvBinding::Neutral(self.neutral(n,remaining)?)}
     }
    };
    // Unchanged frames retain their exact original identity. Rebuilt frames
    // preserve each surviving original variable through an owned neutral alias.
    let unchanged=new_parent==*parent && match (&binding,value){
      (EnvBinding::Free(a),EnvBinding::Free(b))=>a==b,
      (EnvBinding::Closure(a),EnvBinding::Closure(b))=>a==b,
      (EnvBinding::NatLit(a),EnvBinding::NatLit(b))=>a==b,
      (EnvBinding::Neutral(a),EnvBinding::Neutral(b))=>a==b,
      _=>false,
    };
    if unchanged{f.clone()}else{
     let origin=match f.evaluated_binding_origin(){Some((authority,binder))=>Some((authority,self.closure(&binder,remaining)?)),None=>None};
     new_parent.extend_binding_recorded(binding,origin,Some(remaining))?
    }
   }
  };
  self.frames.insert(f.id(),result.clone());Some(result)
 }
}
