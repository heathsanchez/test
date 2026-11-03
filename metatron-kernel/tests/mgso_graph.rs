use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

use metatron_kernel::mgso::SemanticObject;
use metatron_kernel::observation::CheckedDecl;
use metatron_kernel::receipt::{
    ExportIdentity, ReceiptV1, RootManifest, VerificationConfig, build_receipts,
};
use metatron_kernel::receipt_store::{ReceiptStore, ShadowResult};

static NEXT_DIRECTORY: AtomicU64 = AtomicU64::new(0);

struct ScratchDir(PathBuf);

impl ScratchDir {
    fn new() -> Self {
        let unique = NEXT_DIRECTORY.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "nucleus-mgso-graph-{}-{unique}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}

impl Drop for ScratchDir {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}

fn identity() -> ExportIdentity {
    ExportIdentity {
        export_sha256: "a".repeat(64),
        export_format: "3.1.0".into(),
        verifier_build_id: "nucleus-test-build".into(),
        verification_config_sha256: "b".repeat(64),
    }
}

fn events() -> Vec<CheckedDecl> {
    vec![
        CheckedDecl {
            index: 0,
            name: "axiomA".into(),
            kind: "axiom",
        },
        CheckedDecl {
            index: 1,
            name: "theoremB".into(),
            kind: "theorem",
        },
    ]
}

#[test]
fn mgso_graph_builds_deterministic_predecessor_chain() {
    let receipts = build_receipts(&events(), &identity()).unwrap();
    let recreated = build_receipts(&events(), &identity()).unwrap();
    assert_eq!(receipts, recreated);
    assert_eq!(receipts.len(), 2);
    let first = ReceiptV1::from_mgso(&receipts[0]).unwrap();
    let second = ReceiptV1::from_mgso(&receipts[1]).unwrap();
    assert_eq!(first.declaration_index, 0);
    assert_eq!(first.declaration_name, "axiomA");
    assert_eq!(first.predecessor_id, None);
    assert_eq!(second.declaration_name, "theoremB");
    assert_eq!(
        second.predecessor_id.as_deref(),
        Some(receipts[0].id().unwrap().as_str())
    );
    assert_eq!(second.export_sha256, identity().export_sha256);
    assert_eq!(
        second.conclusion,
        "whole-export-accepted-declaration-admitted"
    );
    assert!(receipts[0].encode().unwrap().starts_with(b"MGSO\0\x01"));
}

#[test]
fn mgso_graph_source_context_and_order_each_change_object_identity() {
    let original = build_receipts(&events(), &identity()).unwrap();
    for change in ["export", "build", "config", "format", "order"] {
        let mut candidate = identity();
        let mut sequence = events();
        match change {
            "export" => candidate.export_sha256 = "c".repeat(64),
            "build" => candidate.verifier_build_id = "changed-build".into(),
            "config" => candidate.verification_config_sha256 = "d".repeat(64),
            "format" => candidate.export_format = "changed-parser".into(),
            "order" => {
                sequence[0].name = "changed-first".into();
            }
            _ => unreachable!(),
        }
        let changed = build_receipts(&sequence, &candidate).unwrap();
        assert_ne!(
            original[0].id().unwrap(),
            changed[0].id().unwrap(),
            "{change}"
        );
        assert_ne!(
            original[1].id().unwrap(),
            changed[1].id().unwrap(),
            "{change}"
        );
    }
}

#[test]
fn mgso_graph_large_accepted_export_uses_bounded_pages() {
    // Previous v1 shadow stores stopped at 10,000 objects or 1 MiB of JSON
    // root IDs. Authentic Mathlib has far more declarations; this is a
    // structural store test, not a simulated kernel ACCEPT.
    let scratch = ScratchDir::new();
    let accepted = (0..12_001)
        .map(|index| CheckedDecl {
            index,
            name: format!("source.theorem_{index}"),
            kind: "theorem",
        })
        .collect::<Vec<_>>();
    let objects = build_receipts(&accepted, &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &objects).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    store.write_accepted(&objects, &manifest).unwrap();
    let root_bytes = fs::read(store.manifest_path()).unwrap();
    let root: serde_json::Value = serde_json::from_slice(&root_bytes).unwrap();
    assert_eq!(root["schema_version"], 2);
    assert_eq!(root["declarations"], 12_001);
    let pages = root["page_ids"].as_array().unwrap();
    assert!(pages.len() > 1 && pages.len() < 128, "pages={}", pages.len());
    assert!(root_bytes.len() < 1024 * 1024);
    assert_eq!(
        fs::read_dir(scratch.0.join("objects")).unwrap().count(),
        pages.len(),
        "paged graph must not write one file per declaration"
    );
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::CandidateMatch {
            declarations: 12_001,
            ..
        }
    ));

    // Exact source/configuration changes invalidate the whole conservative
    // graph. No result from this test authorizes cached acceptance.
    let mut changed = identity();
    changed.export_sha256 = "f".repeat(64);
    assert!(matches!(store.read_shadow(&changed), ShadowResult::Stale(_)));

    // Reordering complete, content-addressed pages is not a legitimate
    // dependency rewrite even when each individual page remains unmodified.
    let mut reordered = root.clone();
    reordered["page_ids"].as_array_mut().unwrap().swap(0, 1);
    fs::write(store.manifest_path(), serde_json::to_vec(&reordered).unwrap()).unwrap();
    assert!(matches!(store.read_shadow(&identity()), ShadowResult::Unknown(_)));
    fs::write(store.manifest_path(), &root_bytes).unwrap();

    let second_page = store.object_path(pages[1].as_str().unwrap()).unwrap();
    let missing_path = scratch.0.join("quarantined-page");
    fs::rename(&second_page, &missing_path).unwrap();
    assert!(matches!(store.read_shadow(&identity()), ShadowResult::Unknown(_)));
    fs::rename(&missing_path, &second_page).unwrap();
    assert!(matches!(
        store.read_shadow(&identity()), ShadowResult::CandidateMatch { .. }
    ));

    // Each page, not just the manifest, must be rehashed and decoded.
    let first_id = pages[0].as_str().unwrap();
    fs::write(store.object_path(first_id).unwrap(), b"forged:ACCEPT").unwrap();
    assert!(matches!(store.read_shadow(&identity()), ShadowResult::Unknown(_)));
}

#[test]
fn mgso_graph_mathlib_scale_paging_is_idempotent_and_bounded() {
    // This is *synthetic accepted event data*: it validates storage scaling,
    // not acceptance of the corresponding real Mathlib export.
    let scratch = ScratchDir::new();
    let accepted = (0..130_001)
        .map(|index| CheckedDecl {
            index,
            name: format!("Mathlib.synthetic.namespace.theorem_{index}"),
            kind: "theorem",
        })
        .collect::<Vec<_>>();
    let objects = build_receipts(&accepted, &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &objects).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    let begin = std::time::Instant::now();
    store.write_accepted(&objects, &manifest).unwrap();
    let write_seconds = begin.elapsed().as_secs_f64();
    let bytes = fs::read(store.manifest_path()).unwrap();
    let manifest_doc: serde_json::Value = serde_json::from_slice(&bytes).unwrap();
    let pages = manifest_doc["page_ids"].as_array().unwrap().len();
    assert_eq!(manifest_doc["declarations"], 130_001);
    assert!(pages > 10 && pages < 512, "pages={pages}");
    assert!(bytes.len() < 1024 * 1024);
    let root_before = bytes;
    let read_begin = std::time::Instant::now();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::CandidateMatch { declarations: 130_001, .. }
    ));
    let read_seconds = read_begin.elapsed().as_secs_f64();
    let disk_bytes = fs::read_dir(scratch.0.join("objects"))
        .unwrap()
        .map(|entry| entry.unwrap().metadata().unwrap().len())
        .sum::<u64>();
    let repeat = std::time::Instant::now();
    store.write_accepted(&objects, &manifest).unwrap();
    let rewrite_seconds = repeat.elapsed().as_secs_f64();
    assert_eq!(fs::read(store.manifest_path()).unwrap(), root_before);
    assert_eq!(fs::read_dir(scratch.0.join("objects")).unwrap().count(), pages);
    println!(
        "NUCLEUS_MGSO_STRESS:declarations=130001;pages={pages};disk_bytes={disk_bytes};write_seconds={write_seconds:.3};read_seconds={read_seconds:.3};idempotent_write_seconds={rewrite_seconds:.3};accept_authority=none"
    );
}

#[test]
fn mgso_graph_configuration_digest_is_deterministic_and_sensitive_to_policy() {
    let baseline = VerificationConfig {
        export_format: "3.1.0".into(),
        judgment_steps: 65_536,
        delta_policy: "GuardedSemanticFallback".into(),
        compiled_features: vec!["diagnostics".into(), "native".into()],
        nucleus_flags: vec![("NUCLEUS_EXPERIMENT".into(), "off".into())],
    };
    let mut reordered = baseline.clone();
    reordered.compiled_features.reverse();
    assert_eq!(baseline.sha256(), reordered.sha256());
    reordered.judgment_steps -= 1;
    assert_ne!(baseline.sha256(), reordered.sha256());
    reordered = baseline.clone();
    reordered.nucleus_flags[0].1 = "on".into();
    assert_ne!(baseline.sha256(), reordered.sha256());
}

#[test]
fn mgso_graph_shadow_reads_across_reopened_store_without_acceptance_authority() {
    let scratch = ScratchDir::new();
    let receipts = build_receipts(&events(), &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &receipts).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
    store.write_accepted(&receipts, &manifest).unwrap();
    let reopened = ReceiptStore::new(scratch.0.clone());
    assert!(matches!(
        reopened.read_shadow(&identity()),
        ShadowResult::CandidateMatch {
            declarations: 2,
            ..
        }
    ));
    let mut stale = identity();
    stale.verification_config_sha256 = "e".repeat(64);
    assert!(matches!(
        reopened.read_shadow(&stale),
        ShadowResult::Stale(_)
    ));
    stale = identity();
    stale.export_sha256 = "f".repeat(64);
    assert!(matches!(
        reopened.read_shadow(&stale),
        ShadowResult::Stale(_)
    ));
}

#[test]
fn mgso_graph_corrupted_or_missing_object_never_matches() {
    let scratch = ScratchDir::new();
    let receipts = build_receipts(&events(), &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &receipts).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    store.write_accepted(&receipts, &manifest).unwrap();
    let object_path = store.object_path(&receipts[0].id().unwrap()).unwrap();
    fs::write(&object_path, b"forged:ACCEPT").unwrap();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
    assert!(store.write_accepted(&receipts, &manifest).is_err());
    fs::remove_file(&object_path).unwrap();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
}

#[test]
fn mgso_graph_duplicate_json_fields_unknown_types_and_broken_chain_fail_closed() {
    let original = build_receipts(&events(), &identity()).unwrap();
    let mut duplicate = original[0].clone();
    let payload = String::from_utf8(duplicate.payload.clone()).unwrap();
    duplicate.payload = payload
        .replacen("{", "{\"conclusion\":\"forged\",", 1)
        .into_bytes();
    assert!(ReceiptV1::from_mgso(&duplicate).is_err());
    let mut unknown = original[0].clone();
    unknown.type_id = "attacker.accept".into();
    assert!(ReceiptV1::from_mgso(&unknown).is_err());
    let mut broken = ReceiptV1::from_mgso(&original[1]).unwrap();
    broken.predecessor_id = Some(format!("semantic:{}", "0".repeat(64)));
    let amended = broken.to_mgso().unwrap();
    assert!(RootManifest::from_receipts(&identity(), &[original[0].clone(), amended]).is_err());
}

#[test]
fn mgso_graph_empty_manifest_is_never_a_verified_proof() {
    let scratch = ScratchDir::new();
    let manifest = RootManifest::from_receipts(&identity(), &[]).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    store.write_accepted(&[], &manifest).unwrap();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::CandidateMatch {
            declarations: 0,
            ..
        }
    ));
}

#[cfg(unix)]
#[test]
fn mgso_graph_symlink_object_is_rejected_on_read_and_write() {
    use std::os::unix::fs::symlink;

    let scratch = ScratchDir::new();
    let receipts = build_receipts(&events(), &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &receipts).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    store.write_accepted(&receipts, &manifest).unwrap();
    let object = store.object_path(&receipts[0].id().unwrap()).unwrap();
    let target = scratch.0.join("target");
    fs::write(&target, receipts[0].encode().unwrap()).unwrap();
    fs::remove_file(&object).unwrap();
    symlink(&target, &object).unwrap();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
    assert!(store.write_accepted(&receipts, &manifest).is_err());
}

#[cfg(unix)]
#[test]
fn mgso_graph_first_write_conflict_never_publishes_root() {
    use std::os::unix::fs::symlink;

    let scratch = ScratchDir::new();
    let receipts = build_receipts(&events(), &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &receipts).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    let object_dir = scratch.0.join("objects");
    fs::create_dir(&object_dir).unwrap();
    let collision = store.object_path(&receipts[0].id().unwrap()).unwrap();
    symlink(scratch.0.join("nonexistent-target"), collision).unwrap();
    assert!(store.write_accepted(&receipts, &manifest).is_err());
    assert!(!store.manifest_path().exists());
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
}

#[test]
fn mgso_graph_oversized_or_duplicate_field_manifest_is_not_admitted() {
    let scratch = ScratchDir::new();
    let receipts = build_receipts(&events(), &identity()).unwrap();
    let manifest = RootManifest::from_receipts(&identity(), &receipts).unwrap();
    let store = ReceiptStore::new(scratch.0.clone());
    store.write_accepted(&receipts, &manifest).unwrap();
    let path = store.manifest_path();
    let original = fs::read_to_string(&path).unwrap();
    fs::write(&path, original.replacen("{", "{\"schema_version\":9,", 1)).unwrap();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
    fs::write(&path, "x".repeat(1024 * 1024 + 1)).unwrap();
    assert!(matches!(
        store.read_shadow(&identity()),
        ShadowResult::Unknown(_)
    ));
}

#[test]
fn mgso_graph_storage_rejects_untrusted_object_path_identity() {
    let scratch = ScratchDir::new();
    let store = ReceiptStore::new(scratch.0.clone());
    assert!(store.object_path("../../etc/passwd").is_err());
    assert!(store.object_path("semantic:broken").is_err());
    let unsupported = SemanticObject {
        type_id: "unknown".into(),
        contract_version: 1,
        interfaces: vec![],
        payload: vec![],
    };
    assert!(ReceiptV1::from_mgso(&unsupported).is_err());
}
