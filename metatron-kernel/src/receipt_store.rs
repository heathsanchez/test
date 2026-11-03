//! Immutable MGSO object store with an atomic, context-bound shadow manifest.
//!
//! A matching shadow root establishes *only* byte/context consistency. It
//! never grants ACCEPT and never skips or substitutes a live kernel judgment.

use std::error::Error;
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use crate::mgso::SemanticObject;
use crate::receipt::{
    ExportIdentity, MAX_GRAPH_DECLARATIONS, MAX_GRAPH_PAGES, MAX_PAGE_OBJECT_BYTES,
    MAX_PAGE_RECEIPTS, MAX_RECEIPT_OBJECT_BYTES, PagedRootManifest, ReceiptError,
    ReceiptPageV1, ReceiptV1, RootManifest, valid_object_id,
};

const MAX_MANIFEST_BYTES: usize = 1024 * 1024;
// Small v1 graphs preserve their canonical format and golden vectors. Larger
// graphs pack receipts into content-addressed MGSO pages, keeping file count
// and manifest size bounded instead of writing 100,000+ tiny objects.
const V1_INLINE_LIMIT: usize = 1024;
const PAGE_TARGET_BYTES: usize = 1024 * 1024;
static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

#[derive(Debug)]
pub enum StoreError {
    Io(std::io::Error),
    Invalid(&'static str),
    Receipt(ReceiptError),
}

impl fmt::Display for StoreError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(f, "shadow store I/O: {error}"),
            Self::Invalid(reason) => write!(f, "shadow store invalid: {reason}"),
            Self::Receipt(error) => write!(f, "{error}"),
        }
    }
}

impl Error for StoreError {}

impl From<std::io::Error> for StoreError {
    fn from(value: std::io::Error) -> Self {
        Self::Io(value)
    }
}

impl From<ReceiptError> for StoreError {
    fn from(value: ReceiptError) -> Self {
        Self::Receipt(value)
    }
}

/// Deliberately has no `Accept` variant or ability to authorize a verdict.
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum ShadowResult {
    CandidateMatch {
        declarations: usize,
        root_id: Option<String>,
    },
    Stale(String),
    Unknown(String),
}

#[derive(Clone, Debug)]
pub struct ReceiptStore {
    root: PathBuf,
}

impl ReceiptStore {
    pub fn new(root: PathBuf) -> Self {
        Self { root }
    }

    pub fn manifest_path(&self) -> PathBuf {
        self.root.join("root.json")
    }

    pub fn object_path(&self, id: &str) -> Result<PathBuf, StoreError> {
        if !valid_object_id(id) {
            return Err(StoreError::Invalid("invalid content ID"));
        }
        let hex = id.strip_prefix("semantic:").expect("validated semantic ID");
        Ok(self.root.join("objects").join(format!("{hex}.mgso")))
    }

    fn ensure_root(&self) -> Result<(), StoreError> {
        fs::create_dir_all(&self.root)?;
        require_directory(&self.root)?;
        let objects = self.root.join("objects");
        fs::create_dir_all(&objects)?;
        require_directory(&objects)?;
        Ok(())
    }

    pub fn write_accepted(
        &self,
        objects: &[SemanticObject],
        manifest: &RootManifest,
    ) -> Result<(), StoreError> {
        // Structural checks cannot attest that a caller ran the kernel. The
        // call site must gate this on an ordinary whole-export ACCEPT.
        let reconstructed = RootManifest::from_receipts(&manifest.identity, objects)?;
        if &reconstructed != manifest {
            return Err(StoreError::Invalid("root/receipt mismatch"));
        }
        if objects.len() > MAX_GRAPH_DECLARATIONS {
            return Err(StoreError::Invalid("too many declarations"));
        }
        let paged = objects.len() > V1_INLINE_LIMIT;
        let (stored, manifest_bytes, object_cap) = if paged {
            let stored = pack_receipt_pages(objects)?;
            let page_ids = stored.iter()
                .map(|object| object.id().map_err(ReceiptError::from))
                .collect::<Result<Vec<_>, _>>()?;
            let paged_manifest = PagedRootManifest {
                identity: manifest.identity.clone(),
                declarations: objects.len(),
                page_ids,
                root_id: manifest.root_id.clone(),
            };
            (stored, paged_manifest.to_bytes()?, MAX_PAGE_OBJECT_BYTES)
        } else {
            (objects.to_vec(), manifest.to_bytes()?, MAX_RECEIPT_OBJECT_BYTES)
        };
        if manifest_bytes.len() > MAX_MANIFEST_BYTES {
            return Err(StoreError::Invalid("manifest too large"));
        }
        let encoded = stored
            .iter()
            .map(|object| {
                let bytes = object.encode().map_err(ReceiptError::from)?;
                if bytes.len() > object_cap {
                    return Err(StoreError::Invalid("object too large"));
                }
                let path = self.object_path(&object.id().map_err(ReceiptError::from)?)?;
                Ok((path, bytes))
            })
            .collect::<Result<Vec<_>, StoreError>>()?;

        self.ensure_root()?;
        for (path, bytes) in encoded {
            if path.exists() || fs::symlink_metadata(&path).is_ok() {
                // An existing ID is immutable; even a byte-identical symlink
                // is not acceptable as an object of the graph.
                if read_bounded(&path, object_cap)? != bytes {
                    return Err(StoreError::Invalid(
                        "existing object disagrees with content ID",
                    ));
                }
                continue;
            }
            let (temp, mut file) = create_temp(&self.root.join("objects"))?;
            write_and_sync(&mut file, &bytes)?;
            drop(file);
            match fs::hard_link(&temp, &path) {
                Ok(()) => {}
                Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                    if read_bounded(&path, object_cap)? != bytes {
                        let _ = fs::remove_file(&temp);
                        return Err(StoreError::Invalid("concurrent object mismatch"));
                    }
                }
                Err(error) => {
                    let _ = fs::remove_file(&temp);
                    return Err(StoreError::Io(error));
                }
            }
            fs::remove_file(&temp)?;
        }
        sync_directory(&self.root.join("objects"))?;
        let (temp, mut file) = create_temp(&self.root)?;
        write_and_sync(&mut file, &manifest_bytes)?;
        drop(file);
        let manifest_path = self.manifest_path();
        if fs::symlink_metadata(&manifest_path).is_ok_and(|info| info.file_type().is_symlink()) {
            let _ = fs::remove_file(&temp);
            return Err(StoreError::Invalid("manifest is a symlink"));
        }
        fs::rename(&temp, &manifest_path)?;
        sync_directory(&self.root)?;
        Ok(())
    }

    pub fn read_shadow(&self, expected: &ExportIdentity) -> ShadowResult {
        match self.read_checked(expected) {
            Ok(result) => result,
            Err(error) => ShadowResult::Unknown(error.to_string()),
        }
    }

    fn read_checked(&self, expected: &ExportIdentity) -> Result<ShadowResult, StoreError> {
        expected.validate()?;
        require_directory(&self.root)?;
        let root_bytes = read_bounded(&self.manifest_path(), MAX_MANIFEST_BYTES)?;
        let header: serde_json::Value = serde_json::from_slice(&root_bytes)
            .map_err(|_| StoreError::Invalid("unparseable root manifest"))?;
        match header.get("schema_version").and_then(serde_json::Value::as_u64) {
            Some(1) => self.read_v1_checked(expected, &root_bytes),
            Some(2) => self.read_v2_checked(expected, &root_bytes),
            _ => Err(StoreError::Invalid("unsupported root manifest schema")),
        }
    }

    fn read_v1_checked(&self, expected: &ExportIdentity, root_bytes: &[u8])
        -> Result<ShadowResult, StoreError>
    {
        let manifest = RootManifest::from_bytes(&root_bytes)?;
        if &manifest.identity != expected {
            return Ok(ShadowResult::Stale(
                "exact export/verifier/config identity differs".into(),
            ));
        }
        require_directory(&self.root.join("objects"))?;
        let mut predecessor_id: Option<String> = None;
        for (position, id) in manifest.object_ids.iter().enumerate() {
            let bytes = read_bounded(&self.object_path(id)?, MAX_RECEIPT_OBJECT_BYTES)?;
            let object =
                SemanticObject::decode(&bytes, MAX_RECEIPT_OBJECT_BYTES).map_err(ReceiptError::from)?;
            if object.id().map_err(ReceiptError::from)? != *id {
                return Err(StoreError::Invalid("corrupt object content ID"));
            }
            let receipt = ReceiptV1::from_mgso(&object)?;
            if receipt.identity() != *expected
                || receipt.declaration_index != position as u64
                || receipt.predecessor_id != predecessor_id
            {
                return Err(StoreError::Invalid(
                    "broken receipt context or predecessor chain",
                ));
            }
            predecessor_id = Some(id.clone());
        }
        if predecessor_id != manifest.root_id {
            return Err(StoreError::Invalid(
                "manifest root differs from final receipt",
            ));
        }
        Ok(ShadowResult::CandidateMatch {
            declarations: manifest.object_ids.len(),
            root_id: manifest.root_id,
        })
    }

    fn read_v2_checked(&self, expected: &ExportIdentity, root_bytes: &[u8])
        -> Result<ShadowResult, StoreError>
    {
        let manifest = PagedRootManifest::from_bytes(root_bytes)?;
        if &manifest.identity != expected {
            return Ok(ShadowResult::Stale(
                "exact export/verifier/config identity differs".into(),
            ));
        }
        require_directory(&self.root.join("objects"))?;
        let mut predecessor_page: Option<String> = None;
        let mut predecessor_receipt: Option<String> = None;
        let mut position = 0usize;
        for (page_index, id) in manifest.page_ids.iter().enumerate() {
            let bytes = read_bounded(&self.object_path(id)?, MAX_PAGE_OBJECT_BYTES)?;
            let object = SemanticObject::decode(&bytes, MAX_PAGE_OBJECT_BYTES)
                .map_err(ReceiptError::from)?;
            if object.id().map_err(ReceiptError::from)? != *id {
                return Err(StoreError::Invalid("corrupt page content ID"));
            }
            let page = ReceiptPageV1::from_mgso(&object)?;
            if page.page_index != page_index || page.predecessor_page_id != predecessor_page {
                return Err(StoreError::Invalid("broken predecessor page chain"));
            }
            for embedded in &page.receipts {
                let receipt = ReceiptV1::from_mgso(embedded)?;
                if receipt.identity() != *expected
                    || receipt.declaration_index != position as u64
                    || receipt.predecessor_id != predecessor_receipt
                {
                    return Err(StoreError::Invalid("broken embedded receipt chain"));
                }
                predecessor_receipt = Some(embedded.id().map_err(ReceiptError::from)?);
                position += 1;
                if position > manifest.declarations {
                    return Err(StoreError::Invalid("page has excess declarations"));
                }
            }
            predecessor_page = Some(id.clone());
        }
        if position != manifest.declarations || predecessor_receipt != manifest.root_id {
            return Err(StoreError::Invalid("paged root and final receipt disagree"));
        }
        Ok(ShadowResult::CandidateMatch {
            declarations: position,
            root_id: manifest.root_id,
        })
    }
}

fn pack_receipt_pages(objects: &[SemanticObject]) -> Result<Vec<SemanticObject>, StoreError> {
    let mut pages = Vec::new();
    let mut start = 0;
    while start < objects.len() {
        if pages.len() >= MAX_GRAPH_PAGES {
            return Err(StoreError::Invalid("too many receipt pages"));
        }
        let mut end = start;
        let mut bytes = 0usize;
        while end < objects.len() && end - start < MAX_PAGE_RECEIPTS {
            let length = objects[end].encode().map_err(ReceiptError::from)?.len();
            if length > MAX_RECEIPT_OBJECT_BYTES {
                return Err(StoreError::Invalid("receipt exceeds single-object bound"));
            }
            if end != start && bytes + 4 + length > PAGE_TARGET_BYTES {
                break;
            }
            bytes += 4 + length;
            end += 1;
        }
        let predecessor_page_id = pages.last()
            .map(|previous: &SemanticObject| previous.id().map_err(ReceiptError::from))
            .transpose()?;
        let page = ReceiptPageV1 {
            page_index: pages.len(),
            predecessor_page_id,
            receipts: objects[start..end].to_vec(),
        };
        pages.push(page.to_mgso()?);
        start = end;
    }
    Ok(pages)
}

fn require_directory(path: &Path) -> Result<(), StoreError> {
    let info = fs::symlink_metadata(path)?;
    if !info.file_type().is_dir() || info.file_type().is_symlink() {
        return Err(StoreError::Invalid("expected non-symlink directory"));
    }
    Ok(())
}

fn read_bounded(path: &Path, cap: usize) -> Result<Vec<u8>, StoreError> {
    let info = fs::symlink_metadata(path)?;
    if !info.file_type().is_file() || info.file_type().is_symlink() || info.len() > cap as u64 {
        return Err(StoreError::Invalid("not a bounded regular file"));
    }
    let file = File::open(path)?;
    let mut result = Vec::new();
    file.take(cap as u64 + 1).read_to_end(&mut result)?;
    if result.len() > cap {
        return Err(StoreError::Invalid("file grew beyond bound"));
    }
    Ok(result)
}

fn create_temp(parent: &Path) -> Result<(PathBuf, File), StoreError> {
    for _ in 0..10 {
        let seq = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let candidate = parent.join(format!(".mgso-{}-{seq}.pending", std::process::id()));
        match OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&candidate)
        {
            Ok(file) => return Ok((candidate, file)),
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(error) => return Err(StoreError::Io(error)),
        }
    }
    Err(StoreError::Invalid("temporary file collision"))
}

fn write_and_sync(file: &mut File, bytes: &[u8]) -> Result<(), StoreError> {
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn sync_directory(path: &Path) -> Result<(), StoreError> {
    #[cfg(unix)]
    File::open(path)?.sync_all()?;
    #[cfg(not(unix))]
    let _ = path;
    Ok(())
}
