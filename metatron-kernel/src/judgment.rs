#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct WarrantId(pub &'static str);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct ObstructionId(pub &'static str);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct ResidualId(pub &'static str);

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Judgment<T> {
    Proven { value: T, warrant: WarrantId },
    Refuted { obstruction: ObstructionId },
    Unknown { residual: ResidualId },
}

impl<T> Judgment<T> {
    pub fn proven(value: T, warrant: &'static str) -> Self {
        Self::Proven {
            value,
            warrant: WarrantId(warrant),
        }
    }

    pub fn refuted(obstruction: &'static str) -> Self {
        Self::Refuted {
            obstruction: ObstructionId(obstruction),
        }
    }

    pub fn unknown(residual: &'static str) -> Self {
        Self::Unknown {
            residual: ResidualId(residual),
        }
    }

    pub fn is_proven(&self) -> bool {
        matches!(self, Self::Proven { .. })
    }

    pub fn is_refuted(&self) -> bool {
        matches!(self, Self::Refuted { .. })
    }

    pub fn is_unknown(&self) -> bool {
        matches!(self, Self::Unknown { .. })
    }
}
