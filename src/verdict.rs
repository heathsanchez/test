#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Verdict {
    Accept,
    Reject,
    Unknown,
    Error,
}

impl Verdict {
    pub const fn exit_code(self) -> i32 {
        match self {
            Self::Accept => 0,
            Self::Reject => 1,
            Self::Unknown => 2,
            Self::Error => 3,
        }
    }
}
