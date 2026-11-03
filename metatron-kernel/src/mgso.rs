//! Canonical MGSO v1 transport. Transport carries no typing authority.
//!
//! This is the Rust counterpart of MathGraph's experimental Crystal
//! SemanticObject envelope, not a Lean verification shortcut.

use std::error::Error;
use std::fmt;

use sha2::{Digest, Sha256};

const MAGIC: &[u8; 6] = b"MGSO\0\x01";

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticObject {
    pub type_id: String,
    pub contract_version: u32,
    pub interfaces: Vec<String>,
    pub payload: Vec<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum MgsoError {
    Malformed(&'static str),
    TooLarge,
}

impl fmt::Display for MgsoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Malformed(reason) => write!(f, "malformed MGSO envelope: {reason}"),
            Self::TooLarge => write!(f, "MGSO length exceeds supported bounds"),
        }
    }
}

impl Error for MgsoError {}

fn pack_text(out: &mut Vec<u8>, text: &str) -> Result<(), MgsoError> {
    let len = u32::try_from(text.len()).map_err(|_| MgsoError::TooLarge)?;
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(text.as_bytes());
    Ok(())
}

impl SemanticObject {
    pub fn encode(&self) -> Result<Vec<u8>, MgsoError> {
        if self.type_id.is_empty() || self.interfaces.iter().any(String::is_empty) {
            return Err(MgsoError::Malformed("empty identifier"));
        }
        let mut interfaces = self.interfaces.clone();
        interfaces.sort_unstable();
        interfaces.dedup();
        let count = u32::try_from(interfaces.len()).map_err(|_| MgsoError::TooLarge)?;
        let payload_len = u64::try_from(self.payload.len()).map_err(|_| MgsoError::TooLarge)?;

        let mut out = Vec::new();
        out.extend_from_slice(MAGIC);
        pack_text(&mut out, &self.type_id)?;
        out.extend_from_slice(&self.contract_version.to_be_bytes());
        out.extend_from_slice(&count.to_be_bytes());
        for interface in &interfaces {
            pack_text(&mut out, interface)?;
        }
        out.extend_from_slice(&payload_len.to_be_bytes());
        out.extend_from_slice(&self.payload);
        Ok(out)
    }

    pub fn decode(bytes: &[u8], max_payload_bytes: usize) -> Result<Self, MgsoError> {
        let mut reader = Reader { bytes, position: 0 };
        if reader.take(MAGIC.len())? != MAGIC {
            return Err(MgsoError::Malformed("unsupported envelope version"));
        }
        let type_id = reader.text()?;
        if type_id.is_empty() {
            return Err(MgsoError::Malformed("empty type ID"));
        }
        let contract_version = reader.u32()?;
        let count = usize::try_from(reader.u32()?).map_err(|_| MgsoError::TooLarge)?;
        if count > reader.remaining() / 4 {
            return Err(MgsoError::Malformed("impossible interface count"));
        }
        let mut interfaces = Vec::new();
        let mut previous: Option<String> = None;
        for _ in 0..count {
            let interface = reader.text()?;
            if interface.is_empty() || previous.as_ref().is_some_and(|last| last >= &interface) {
                return Err(MgsoError::Malformed("interfaces not strictly sorted"));
            }
            previous = Some(interface.clone());
            interfaces.push(interface);
        }
        let payload_len = usize::try_from(reader.u64()?).map_err(|_| MgsoError::TooLarge)?;
        if payload_len > max_payload_bytes {
            return Err(MgsoError::TooLarge);
        }
        let payload = reader.take(payload_len)?.to_vec();
        if reader.remaining() != 0 {
            return Err(MgsoError::Malformed("trailing bytes"));
        }
        Ok(Self {
            type_id,
            contract_version,
            interfaces,
            payload,
        })
    }

    pub fn id(&self) -> Result<String, MgsoError> {
        let encoded = self.encode()?;
        let digest = Sha256::digest(encoded);
        let mut id = String::with_capacity("semantic:".len() + 64);
        id.push_str("semantic:");
        for byte in digest {
            use std::fmt::Write;
            write!(&mut id, "{byte:02x}").expect("writing to String cannot fail");
        }
        Ok(id)
    }
}

struct Reader<'a> {
    bytes: &'a [u8],
    position: usize,
}

impl<'a> Reader<'a> {
    fn remaining(&self) -> usize {
        self.bytes.len() - self.position
    }

    fn take(&mut self, count: usize) -> Result<&'a [u8], MgsoError> {
        let end = self
            .position
            .checked_add(count)
            .ok_or(MgsoError::TooLarge)?;
        let bytes = self
            .bytes
            .get(self.position..end)
            .ok_or(MgsoError::Malformed("truncated record"))?;
        self.position = end;
        Ok(bytes)
    }

    fn u32(&mut self) -> Result<u32, MgsoError> {
        Ok(u32::from_be_bytes(
            self.take(4)?.try_into().expect("exact four bytes"),
        ))
    }

    fn u64(&mut self) -> Result<u64, MgsoError> {
        Ok(u64::from_be_bytes(
            self.take(8)?.try_into().expect("exact eight bytes"),
        ))
    }

    fn text(&mut self) -> Result<String, MgsoError> {
        let len = usize::try_from(self.u32()?).map_err(|_| MgsoError::TooLarge)?;
        let data = self.take(len)?;
        String::from_utf8(data.to_vec()).map_err(|_| MgsoError::Malformed("invalid UTF-8"))
    }
}
