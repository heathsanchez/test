use std::collections::{BTreeMap, HashMap, HashSet};
use std::error::Error;
use std::fmt;

use crate::id::{IdTable, LevelId, NameId};
use crate::judgment::Judgment;
use crate::syntax::Level;

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum LevelTerm {
    Zero,
    Succ(Box<LevelTerm>),
    Max(Box<LevelTerm>, Box<LevelTerm>),
    IMax(Box<LevelTerm>, Box<LevelTerm>),
    Param(String),
}

impl LevelTerm {
    pub fn param(name: impl Into<String>) -> Self {
        Self::Param(name.into())
    }
}

pub fn succ(level: LevelTerm) -> LevelTerm {
    LevelTerm::Succ(Box::new(level))
}

pub fn max(left: LevelTerm, right: LevelTerm) -> LevelTerm {
    match (left, right) {
        (LevelTerm::Zero, right) => right,
        (left, LevelTerm::Zero) => left,
        (left, right) if left == right => left,
        (left, right) => LevelTerm::Max(Box::new(left), Box::new(right)),
    }
}

pub fn level_imax(left: LevelTerm, right: LevelTerm) -> LevelTerm {
    match right {
        LevelTerm::Zero => LevelTerm::Zero,
        right @ LevelTerm::Succ(_) => max(left, right),
        right => LevelTerm::IMax(Box::new(left), Box::new(right)),
    }
}

pub fn imax(left: LevelTerm, right: LevelTerm) -> LevelTerm {
    level_imax(left, right)
}

pub fn level_equal(left: LevelTerm, right: LevelTerm, budget: usize) -> Judgment<()> {
    let mut budget = Budget::new(budget);
    let Ok(left) = simplify(left, &mut budget) else {
        return Judgment::unknown("universe-equality-budget");
    };
    let Ok(right) = simplify(right, &mut budget) else {
        return Judgment::unknown("universe-equality-budget");
    };

    if left == right {
        return Judgment::proven((), "universe-reflexivity");
    }

    let Some(left) = canonical(&left, &mut budget) else {
        return Judgment::unknown("unresolved-imax-case");
    };
    let Some(right) = canonical(&right, &mut budget) else {
        return Judgment::unknown("unresolved-imax-case");
    };
    if budget.exhausted {
        return Judgment::unknown("universe-equality-budget");
    }

    if left == right {
        Judgment::proven((), "canonical-max-successor-algebra")
    } else {
        Judgment::refuted("distinct-canonical-universes")
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum LevelError {
    MissingLevel(LevelId),
    MissingSubstitution(NameId),
    Cycle(LevelId),
    BudgetExhausted,
}

impl fmt::Display for LevelError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingLevel(id) => write!(formatter, "missing level id {}", id.0),
            Self::MissingSubstitution(id) => {
                write!(formatter, "missing substitution for name id {}", id.0)
            }
            Self::Cycle(id) => write!(formatter, "cyclic level graph at id {}", id.0),
            Self::BudgetExhausted => write!(formatter, "level instantiation budget exhausted"),
        }
    }
}

impl Error for LevelError {}

pub fn instantiate_level(
    levels: &IdTable<LevelId, Level>,
    root: LevelId,
    substitution: &HashMap<NameId, LevelTerm>,
    budget: usize,
) -> Result<LevelTerm, LevelError> {
    let mut remaining = budget;
    let mut visiting = HashSet::new();
    instantiate(levels, root, substitution, &mut remaining, &mut visiting)
}

fn instantiate(
    levels: &IdTable<LevelId, Level>,
    id: LevelId,
    substitution: &HashMap<NameId, LevelTerm>,
    remaining: &mut usize,
    visiting: &mut HashSet<LevelId>,
) -> Result<LevelTerm, LevelError> {
    if *remaining == 0 {
        return Err(LevelError::BudgetExhausted);
    }
    *remaining -= 1;
    if !visiting.insert(id) {
        return Err(LevelError::Cycle(id));
    }
    let level = levels.get(id).ok_or(LevelError::MissingLevel(id))?;
    let result = match level {
        Level::Zero => Ok(LevelTerm::Zero),
        Level::Succ(inner) => {
            instantiate(levels, *inner, substitution, remaining, visiting).map(succ)
        }
        Level::Max(left, right) => {
            let left = instantiate(levels, *left, substitution, remaining, visiting)?;
            let right = instantiate(levels, *right, substitution, remaining, visiting)?;
            Ok(max(left, right))
        }
        Level::IMax(left, right) => {
            let left = instantiate(levels, *left, substitution, remaining, visiting)?;
            let right = instantiate(levels, *right, substitution, remaining, visiting)?;
            Ok(level_imax(left, right))
        }
        Level::Param(name) => substitution
            .get(name)
            .cloned()
            .ok_or(LevelError::MissingSubstitution(*name)),
    };
    visiting.remove(&id);
    result
}

fn simplify(level: LevelTerm, budget: &mut Budget) -> Result<LevelTerm, ()> {
    budget.tick()?;
    match level {
        LevelTerm::Zero | LevelTerm::Param(_) => Ok(level),
        LevelTerm::Succ(inner) => Ok(succ(simplify(*inner, budget)?)),
        LevelTerm::Max(left, right) => {
            let left = simplify(*left, budget)?;
            let right = simplify(*right, budget)?;
            Ok(max(left, right))
        }
        LevelTerm::IMax(left, right) => {
            let left = simplify(*left, budget)?;
            let right = simplify(*right, budget)?;
            Ok(level_imax(left, right))
        }
    }
}

#[derive(Debug, Eq, PartialEq)]
struct CanonicalLevel {
    constant: usize,
    parameters: BTreeMap<String, usize>,
}

fn canonical(level: &LevelTerm, budget: &mut Budget) -> Option<CanonicalLevel> {
    let mut result = CanonicalLevel {
        constant: 0,
        parameters: BTreeMap::new(),
    };
    if !collect(level, 0, &mut result, budget) {
        return None;
    }
    if result
        .parameters
        .values()
        .any(|offset| *offset >= result.constant)
    {
        result.constant = 0;
    }
    Some(result)
}

fn collect(
    level: &LevelTerm,
    offset: usize,
    result: &mut CanonicalLevel,
    budget: &mut Budget,
) -> bool {
    if budget.tick().is_err() {
        return false;
    }
    match level {
        LevelTerm::Zero => result.constant = result.constant.max(offset),
        LevelTerm::Succ(inner) => {
            let Some(offset) = offset.checked_add(1) else {
                budget.exhausted = true;
                return false;
            };
            return collect(inner, offset, result, budget);
        }
        LevelTerm::Max(left, right) => {
            return collect(left, offset, result, budget) && collect(right, offset, result, budget);
        }
        LevelTerm::IMax(_, _) => return false,
        LevelTerm::Param(name) => {
            let entry = result.parameters.entry(name.clone()).or_default();
            *entry = (*entry).max(offset);
        }
    }
    true
}

struct Budget {
    remaining: usize,
    exhausted: bool,
}

impl Budget {
    fn new(remaining: usize) -> Self {
        Self {
            remaining,
            exhausted: false,
        }
    }

    fn tick(&mut self) -> Result<(), ()> {
        if self.remaining == 0 {
            self.exhausted = true;
            Err(())
        } else {
            self.remaining -= 1;
            Ok(())
        }
    }
}
