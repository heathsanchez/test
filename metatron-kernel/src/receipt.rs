//! Versioned, deterministic receipts for an *observation-only* Nucleus graph.
//!
//! A receipt is not a proof. Its `conclusion` is untrusted serialized data;
//! only a fresh, independent Nucleus invocation can return a kernel verdict.

use std::error::Error;
use std::fmt;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::mgso::{MgsoError, SemanticObject};
use crate::observation::CheckedDecl;

pub const RECEIPT_TYPE_ID: &str = "nucleus.declaration_receipt";
pub const RECEIPT_INTERFACE: &str = "nucleus.checked-declaration.v1";
pub const RECEIPT_CONCLUSION: &str = "whole-export-accepted-declaration-admitted";

#[derive(Debug)]
pub enum ReceiptError {
    Malformed(&'static str),
    Envelope(MgsoError),
}

impl fmt::Display for ReceiptError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Malformed(reason) => write!(f, "invalid Nucleus receipt: {reason}"),
            Self::Envelope(error) => write!(f, "{error}"),
        }
    }
}

impl Error for ReceiptError {}

impl From<MgsoError> for ReceiptError {
    fn from(value: MgsoError) -> Self {
        Self::Envelope(value)
    }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

pub fn valid_digest(digest: &str) -> bool {
    digest.len() == 64
        && digest
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

pub fn valid_object_id(id: &str) -> bool {
    id.strip_prefix("semantic:").is_some_and(valid_digest)
}

fn canonical_parse(bytes: &[u8]) -> Result<Value, ReceiptError> {
    let parsed: Value =
        serde_json::from_slice(bytes).map_err(|_| ReceiptError::Malformed("invalid JSON"))?;
    let canonical = serde_json::to_vec(&parsed)
        .map_err(|_| ReceiptError::Malformed("cannot serialize JSON"))?;
    if canonical != bytes {
        return Err(ReceiptError::Malformed(
            "noncanonical or duplicate JSON fields",
        ));
    }
    Ok(parsed)
}

fn field_str<'a>(value: &'a Value, key: &str) -> Result<&'a str, ReceiptError> {
    value
        .get(key)
        .and_then(Value::as_str)
        .ok_or(ReceiptError::Malformed("missing string field"))
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExportIdentity {
    pub export_sha256: String,
    pub export_format: String,
    pub verifier_build_id: String,
    pub verification_config_sha256: String,
}

impl ExportIdentity {
    pub fn validate(&self) -> Result<(), ReceiptError> {
        if !valid_digest(&self.export_sha256)
            || !valid_digest(&self.verification_config_sha256)
            || self.export_format.is_empty()
            || self.verifier_build_id.is_empty()
            || self.export_format.len() > 128
            || self.verifier_build_id.len() > 1024
        {
            return Err(ReceiptError::Malformed("invalid export identity"));
        }
        Ok(())
    }

    fn to_json(&self) -> Value {
        json!({
            "export_sha256": self.export_sha256,
            "export_format": self.export_format,
            "verifier_build_id": self.verifier_build_id,
            "verification_config_sha256": self.verification_config_sha256,
        })
    }

    fn from_json(value: &Value) -> Result<Self, ReceiptError> {
        if value.as_object().is_none_or(|map| map.len() != 4) {
            return Err(ReceiptError::Malformed("unexpected export identity fields"));
        }
        let identity = Self {
            export_sha256: field_str(value, "export_sha256")?.into(),
            export_format: field_str(value, "export_format")?.into(),
            verifier_build_id: field_str(value, "verifier_build_id")?.into(),
            verification_config_sha256: field_str(value, "verification_config_sha256")?.into(),
        };
        identity.validate()?;
        Ok(identity)
    }
}

/// Verifier-affecting settings are hashed into the graph identity, never used
/// as acceptance authority. Flags must be captured at each invocation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerificationConfig {
    pub export_format: String,
    pub judgment_steps: u64,
    pub delta_policy: String,
    pub compiled_features: Vec<String>,
    pub nucleus_flags: Vec<(String, String)>,
}

impl VerificationConfig {
    pub fn sha256(&self) -> String {
        let mut compiled_features = self.compiled_features.clone();
        compiled_features.sort();
        compiled_features.dedup();
        let mut nucleus_flags = self.nucleus_flags.clone();
        nucleus_flags.sort();
        let canonical = json!({
            "schema_version": 1,
            "export_format": self.export_format,
            "judgment_steps": self.judgment_steps,
            "delta_policy": self.delta_policy,
            "compiled_features": compiled_features,
            "nucleus_flags": nucleus_flags,
        });
        sha256_hex(&serde_json::to_vec(&canonical).expect("canonical JSON serialization"))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReceiptV1 {
    pub export_sha256: String,
    pub export_format: String,
    pub verifier_build_id: String,
    pub verification_config_sha256: String,
    pub declaration_index: u64,
    pub declaration_name: String,
    pub declaration_kind: String,
    pub predecessor_id: Option<String>,
    pub conclusion: String,
}

impl ReceiptV1 {
    fn validate(&self) -> Result<(), ReceiptError> {
        let identity = ExportIdentity {
            export_sha256: self.export_sha256.clone(),
            export_format: self.export_format.clone(),
            verifier_build_id: self.verifier_build_id.clone(),
            verification_config_sha256: self.verification_config_sha256.clone(),
        };
        identity.validate()?;
        if self.declaration_name.is_empty()
            || self.declaration_name.len() > 4096
            || !matches!(
                self.declaration_kind.as_str(),
                "axiom" | "definition" | "opaque" | "theorem" | "quot" | "inductive"
            )
            || self
                .predecessor_id
                .as_deref()
                .is_some_and(|id| !valid_object_id(id))
            || self.conclusion != RECEIPT_CONCLUSION
        {
            return Err(ReceiptError::Malformed(
                "invalid declaration receipt fields",
            ));
        }
        Ok(())
    }

    pub fn to_mgso(&self) -> Result<SemanticObject, ReceiptError> {
        self.validate()?;
        let payload = serde_json::to_vec(&json!({
            "export_sha256": self.export_sha256,
            "export_format": self.export_format,
            "verifier_build_id": self.verifier_build_id,
            "verification_config_sha256": self.verification_config_sha256,
            "declaration_index": self.declaration_index,
            "declaration_name": self.declaration_name,
            "declaration_kind": self.declaration_kind,
            "predecessor_id": self.predecessor_id,
            "conclusion": self.conclusion,
        }))
        .map_err(|_| ReceiptError::Malformed("cannot encode receipt JSON"))?;
        Ok(SemanticObject {
            type_id: RECEIPT_TYPE_ID.into(),
            contract_version: 1,
            interfaces: vec![RECEIPT_INTERFACE.into()],
            payload,
        })
    }

    pub fn from_mgso(object: &SemanticObject) -> Result<Self, ReceiptError> {
        if object.type_id != RECEIPT_TYPE_ID
            || object.contract_version != 1
            || object.interfaces != [RECEIPT_INTERFACE]
            || object.payload.len() > 65536
        {
            return Err(ReceiptError::Malformed("unknown receipt contract"));
        }
        let value = canonical_parse(&object.payload)?;
        if value.as_object().is_none_or(|map| map.len() != 9) {
            return Err(ReceiptError::Malformed("unexpected receipt fields"));
        }
        let receipt = Self {
            export_sha256: field_str(&value, "export_sha256")?.into(),
            export_format: field_str(&value, "export_format")?.into(),
            verifier_build_id: field_str(&value, "verifier_build_id")?.into(),
            verification_config_sha256: field_str(&value, "verification_config_sha256")?.into(),
            declaration_index: value
                .get("declaration_index")
                .and_then(Value::as_u64)
                .ok_or(ReceiptError::Malformed("invalid declaration index"))?,
            declaration_name: field_str(&value, "declaration_name")?.into(),
            declaration_kind: field_str(&value, "declaration_kind")?.into(),
            predecessor_id: match value.get("predecessor_id") {
                Some(Value::Null) => None,
                Some(Value::String(id)) => Some(id.clone()),
                _ => return Err(ReceiptError::Malformed("invalid predecessor")),
            },
            conclusion: field_str(&value, "conclusion")?.into(),
        };
        receipt.validate()?;
        Ok(receipt)
    }

    pub fn identity(&self) -> ExportIdentity {
        ExportIdentity {
            export_sha256: self.export_sha256.clone(),
            export_format: self.export_format.clone(),
            verifier_build_id: self.verifier_build_id.clone(),
            verification_config_sha256: self.verification_config_sha256.clone(),
        }
    }
}

pub fn build_receipts(
    accepted: &[CheckedDecl],
    identity: &ExportIdentity,
) -> Result<Vec<SemanticObject>, ReceiptError> {
    identity.validate()?;
    let mut objects: Vec<SemanticObject> = Vec::with_capacity(accepted.len());
    let mut predecessor_id = None;
    for (position, event) in accepted.iter().enumerate() {
        if event.index != position {
            return Err(ReceiptError::Malformed(
                "noncontiguous declaration sequence",
            ));
        }
        let receipt = ReceiptV1 {
            export_sha256: identity.export_sha256.clone(),
            export_format: identity.export_format.clone(),
            verifier_build_id: identity.verifier_build_id.clone(),
            verification_config_sha256: identity.verification_config_sha256.clone(),
            declaration_index: position as u64,
            declaration_name: event.name.clone(),
            declaration_kind: event.kind.into(),
            predecessor_id,
            conclusion: RECEIPT_CONCLUSION.into(),
        };
        let object = receipt.to_mgso()?;
        predecessor_id = Some(object.id()?);
        objects.push(object);
    }
    Ok(objects)
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RootManifest {
    pub identity: ExportIdentity,
    pub object_ids: Vec<String>,
    pub root_id: Option<String>,
}

impl RootManifest {
    pub fn from_receipts(
        identity: &ExportIdentity,
        objects: &[SemanticObject],
    ) -> Result<Self, ReceiptError> {
        identity.validate()?;
        let mut object_ids = Vec::with_capacity(objects.len());
        for (position, object) in objects.iter().enumerate() {
            let receipt = ReceiptV1::from_mgso(object)?;
            if receipt.identity() != *identity
                || receipt.declaration_index != position as u64
                || receipt.predecessor_id != object_ids.last().cloned()
            {
                return Err(ReceiptError::Malformed("invalid predecessor or context"));
            }
            object_ids.push(object.id()?);
        }
        Ok(Self {
            identity: identity.clone(),
            root_id: object_ids.last().cloned(),
            object_ids,
        })
    }

    pub fn to_bytes(&self) -> Result<Vec<u8>, ReceiptError> {
        self.identity.validate()?;
        if self.object_ids.iter().any(|id| !valid_object_id(id))
            || self.root_id != self.object_ids.last().cloned()
        {
            return Err(ReceiptError::Malformed("invalid manifest IDs"));
        }
        serde_json::to_vec(&json!({
            "schema_version": 1,
            "identity": self.identity.to_json(),
            "object_ids": self.object_ids,
            "root_id": self.root_id,
        }))
        .map_err(|_| ReceiptError::Malformed("cannot encode manifest"))
    }

    pub fn from_bytes(bytes: &[u8]) -> Result<Self, ReceiptError> {
        if bytes.len() > 1024 * 1024 {
            return Err(ReceiptError::Malformed("manifest too large"));
        }
        let value = canonical_parse(bytes)?;
        if value.as_object().is_none_or(|map| map.len() != 4)
            || value.get("schema_version").and_then(Value::as_u64) != Some(1)
        {
            return Err(ReceiptError::Malformed("unsupported manifest schema"));
        }
        let identity = ExportIdentity::from_json(
            value
                .get("identity")
                .ok_or(ReceiptError::Malformed("missing identity"))?,
        )?;
        let ids = value
            .get("object_ids")
            .and_then(Value::as_array)
            .ok_or(ReceiptError::Malformed("invalid object list"))?;
        if ids.len() > 10_000 {
            return Err(ReceiptError::Malformed("too many objects"));
        }
        let object_ids = ids
            .iter()
            .map(|item| {
                let id = item
                    .as_str()
                    .ok_or(ReceiptError::Malformed("invalid object ID"))?;
                if !valid_object_id(id) {
                    return Err(ReceiptError::Malformed("invalid object ID"));
                }
                Ok(id.to_string())
            })
            .collect::<Result<Vec<_>, ReceiptError>>()?;
        let root_id = match value.get("root_id") {
            Some(Value::Null) => None,
            Some(Value::String(id)) if valid_object_id(id) => Some(id.clone()),
            _ => return Err(ReceiptError::Malformed("invalid root ID")),
        };
        let manifest = Self {
            identity,
            object_ids,
            root_id,
        };
        manifest.to_bytes()?;
        if manifest.root_id != manifest.object_ids.last().cloned() {
            return Err(ReceiptError::Malformed("root does not match chain"));
        }
        Ok(manifest)
    }
}
