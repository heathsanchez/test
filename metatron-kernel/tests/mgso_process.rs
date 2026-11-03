use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};

use metatron_kernel::receipt::RootManifest;
use metatron_kernel::receipt_store::{ReceiptStore, ShadowResult};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const VALID: &str = include_str!("fixtures/good-theorem-use.ndjson");
const FORGED: &str = include_str!("fixtures/bad-self-theorem.ndjson");
const UNKNOWN: &str = include_str!("fixtures/unsupported-inductive.ndjson");

struct ScratchDir(PathBuf);

impl ScratchDir {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "nucleus-mgso-process-{}-{}-{}",
            std::process::id(),
            NEXT_TEMP.fetch_add(1, Ordering::Relaxed),
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

fn invoke(input: &str, shadow: Option<&Path>) -> Output {
    let mut command = Command::new(env!("CARGO_BIN_EXE_metatron-kernel"));
    if let Some(path) = shadow {
        command.arg("--mgso-shadow-dir").arg(path);
    }
    let mut child = command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(input.as_bytes())
        .unwrap();
    child.wait_with_output().unwrap()
}

fn compare_outputs(original: &Output, shadow: &Output) {
    assert_eq!(shadow.status.code(), original.status.code());
    assert_eq!(shadow.stdout, original.stdout);
}

#[test]
fn mgso_process_default_and_shadow_verdicts_match_for_authentic_and_adversarial() {
    let dir = ScratchDir::new();
    for input in [VALID, FORGED, UNKNOWN, "{not json}\n"] {
        let ordinary = invoke(input, None);
        let shadow = invoke(input, Some(&dir.0));
        compare_outputs(&ordinary, &shadow);
        assert!(String::from_utf8_lossy(&shadow.stderr).contains("NUCLEUS_MGSO_SHADOW"));
    }
}

#[test]
fn mgso_process_two_separate_processes_reuse_byte_context_candidates_only() {
    let dir = ScratchDir::new();
    let ordinary = invoke(VALID, None);
    let first = invoke(VALID, Some(&dir.0));
    compare_outputs(&ordinary, &first);
    assert!(String::from_utf8_lossy(&first.stderr).contains("status=unknown"));
    assert!(dir.0.join("root.json").exists());
    let second = invoke(VALID, Some(&dir.0));
    compare_outputs(&ordinary, &second);
    assert!(String::from_utf8_lossy(&second.stderr).contains("status=candidate-match"));

    let manifest = RootManifest::from_bytes(&fs::read(dir.0.join("root.json")).unwrap()).unwrap();
    assert_eq!(manifest.object_ids.len(), 2);
    assert!(matches!(
        ReceiptStore::new(dir.0.clone()).read_shadow(&manifest.identity),
        ShadowResult::CandidateMatch {
            declarations: 2,
            ..
        }
    ));
}

#[test]
fn mgso_process_source_mutation_stales_without_changing_checker_decision() {
    let dir = ScratchDir::new();
    invoke(VALID, Some(&dir.0));
    let changed = VALID.replace('\n', "\r\n");
    let ordinary = invoke(&changed, None);
    let observed = invoke(&changed, Some(&dir.0));
    compare_outputs(&ordinary, &observed);
    assert!(String::from_utf8_lossy(&observed.stderr).contains("status=stale"));
}

#[test]
fn mgso_process_changed_verifier_flag_is_stale_even_for_identical_source() {
    let dir = ScratchDir::new();
    let baseline = invoke(VALID, None);
    invoke(VALID, Some(&dir.0));
    let mut command = Command::new(env!("CARGO_BIN_EXE_metatron-kernel"));
    let mut child = command
        .arg("--mgso-shadow-dir")
        .arg(&dir.0)
        .env("NUCLEUS_INFERENCE_BOUNDARY", "different")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(VALID.as_bytes())
        .unwrap();
    let after = child.wait_with_output().unwrap();
    compare_outputs(&baseline, &after);
    assert!(String::from_utf8_lossy(&after.stderr).contains("status=stale"));
}

#[test]
fn mgso_process_forged_invalidated_or_corrupt_receipts_never_override_fresh_checker() {
    let dir = ScratchDir::new();
    invoke(VALID, Some(&dir.0));
    let manifest = RootManifest::from_bytes(&fs::read(dir.0.join("root.json")).unwrap()).unwrap();
    let store = ReceiptStore::new(dir.0.clone());
    let first_object = store.object_path(&manifest.object_ids[0]).unwrap();
    fs::write(&first_object, b"MGSO\0\x01\0\0\0\0forged-ACCEPT").unwrap();

    let ordinary = invoke(VALID, None);
    let after_corruption = invoke(VALID, Some(&dir.0));
    compare_outputs(&ordinary, &after_corruption);
    assert!(String::from_utf8_lossy(&after_corruption.stderr).contains("status=unknown"));

    let ordinary_forged = invoke(FORGED, None);
    let forbidden = invoke(FORGED, Some(&dir.0));
    compare_outputs(&ordinary_forged, &forbidden);
    assert_ne!(ordinary.status.code(), ordinary_forged.status.code());
}

#[test]
fn mgso_process_bad_root_or_missing_directory_is_only_a_diagnostic() {
    let dir = ScratchDir::new();
    let ordinary = invoke(VALID, None);
    fs::write(dir.0.join("root.json"), b"{\"schema_version\":9}").unwrap();
    let bad = invoke(VALID, Some(&dir.0));
    compare_outputs(&ordinary, &bad);
    assert!(String::from_utf8_lossy(&bad.stderr).contains("status=unknown"));
    let missing = dir.0.join("not-created");
    let fresh = invoke(VALID, Some(&missing));
    compare_outputs(&ordinary, &fresh);
}

#[test]
fn mgso_process_concurrent_writers_leave_complete_content_addressed_root() {
    let dir = ScratchDir::new();
    let base = invoke(VALID, None);
    let cloned = dir.0.clone();
    let first = std::thread::spawn(move || invoke(VALID, Some(&cloned)));
    let second = invoke(VALID, Some(&dir.0));
    let first = first.join().unwrap();
    compare_outputs(&base, &first);
    compare_outputs(&base, &second);
    let root = RootManifest::from_bytes(&fs::read(dir.0.join("root.json")).unwrap()).unwrap();
    assert!(matches!(
        ReceiptStore::new(dir.0.clone()).read_shadow(&root.identity),
        ShadowResult::CandidateMatch {
            declarations: 2,
            ..
        }
    ));
}

#[test]
fn mgso_process_invalid_flag_is_explicit_error() {
    let status = Command::new(env!("CARGO_BIN_EXE_metatron-kernel"))
        .arg("--mgso-shadow-dir")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .unwrap();
    assert!(!status.success());
}

#[test]
fn mgso_process_unknown_or_parse_error_never_creates_a_root() {
    for input in [UNKNOWN, "{not json}\n", FORGED] {
        let dir = ScratchDir::new();
        let ordinary = invoke(input, None);
        let shadow = invoke(input, Some(&dir.0));
        compare_outputs(&ordinary, &shadow);
        assert!(!dir.0.join("root.json").exists());
    }
}

#[cfg(unix)]
#[test]
fn mgso_process_symlink_manifest_does_not_change_external_target() {
    use std::os::unix::fs::symlink;

    let dir = ScratchDir::new();
    let target = dir.0.join("outside-root-sentinel");
    let sentinel = b"private-sentinel";
    fs::write(&target, sentinel).unwrap();
    symlink(&target, dir.0.join("root.json")).unwrap();
    let original = invoke(VALID, None);
    let observed = invoke(VALID, Some(&dir.0));
    compare_outputs(&original, &observed);
    assert_eq!(&fs::read(&target).unwrap(), sentinel);
    assert!(String::from_utf8_lossy(&observed.stderr).contains("write=unknown"));
}
