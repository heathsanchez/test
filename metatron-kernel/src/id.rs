use std::collections::HashMap;
use std::collections::hash_map::Entry;
use std::error::Error;
use std::fmt;
use std::hash::{BuildHasherDefault, Hasher};
use std::marker::PhantomData;

#[derive(Default)]
struct U64IdentityHasher(u64);

impl Hasher for U64IdentityHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }

    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        // IdTable is keyed only by u64. Keep this total for Hash's generic
        // contract, but the hot path uses write_u64 below.
        let mut value = 0u64;
        for (shift, byte) in bytes.iter().take(8).enumerate() {
            value |= u64::from(*byte) << (shift * 8);
        }
        self.0 = value;
    }

    #[inline]
    fn write_u64(&mut self, value: u64) {
        self.0 = value;
    }
}

type U64BuildHasher = BuildHasherDefault<U64IdentityHasher>;

macro_rules! define_id {
    ($name:ident, $kind:literal) => {
        #[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub struct $name(pub u64);

        impl TableId for $name {
            const KIND: &'static str = $kind;

            fn raw(self) -> u64 {
                self.0
            }
        }
    };
}

pub trait TableId: Copy {
    const KIND: &'static str;

    fn raw(self) -> u64;
}

define_id!(NameId, "name");
define_id!(LevelId, "level");
define_id!(ExprId, "expression");
define_id!(DeclId, "declaration");

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DuplicateId {
    kind: &'static str,
    id: u64,
}

impl DuplicateId {
    pub fn kind(&self) -> &'static str {
        self.kind
    }

    pub fn id(&self) -> u64 {
        self.id
    }
}

impl fmt::Display for DuplicateId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "duplicate {} id {}", self.kind, self.id)
    }
}

impl Error for DuplicateId {}

#[derive(Clone, Debug)]
pub struct IdTable<I, T> {
    entries: HashMap<u64, T, U64BuildHasher>,
    marker: PhantomData<fn(I) -> I>,
}

impl<I, T> Default for IdTable<I, T> {
    fn default() -> Self {
        Self {
            entries: HashMap::with_hasher(U64BuildHasher::default()),
            marker: PhantomData,
        }
    }
}

impl<I: TableId, T> IdTable<I, T> {
    pub fn insert(&mut self, id: I, value: T) -> Result<(), DuplicateId> {
        let raw = id.raw();
        match self.entries.entry(raw) {
            Entry::Vacant(entry) => {
                entry.insert(value);
                Ok(())
            }
            Entry::Occupied(_) => Err(DuplicateId {
                kind: I::KIND,
                id: raw,
            }),
        }
    }

    pub fn get(&self, id: I) -> Option<&T> {
        self.entries.get(&id.raw())
    }

    pub fn contains(&self, id: I) -> bool {
        self.entries.contains_key(&id.raw())
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub fn values(&self) -> impl Iterator<Item = &T> {
        self.entries.values()
    }
}
