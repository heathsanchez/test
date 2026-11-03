//! Explicit observation of completed Nucleus checking.
//!
//! Candidate events are never independent proof or cache authority. The
//! public observation entry discards all events unless the whole export,
//! including its outer guards, returns ACCEPT.

use std::io::{self, Read};

use sha2::{Digest, Sha256};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckedDecl {
    pub index: usize,
    pub name: String,
    pub kind: &'static str,
}

pub(crate) struct Sha256Read<R> {
    reader: R,
    sha256: Sha256,
}

impl<R: Read> Sha256Read<R> {
    pub(crate) fn new(reader: R) -> Self {
        Self {
            reader,
            sha256: Sha256::new(),
        }
    }

    pub(crate) fn finish(self) -> [u8; 32] {
        self.sha256.finalize().into()
    }
}

impl<R: Read> Read for Sha256Read<R> {
    fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
        let count = self.reader.read(buffer)?;
        self.sha256.update(&buffer[..count]);
        Ok(count)
    }
}
