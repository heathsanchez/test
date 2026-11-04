use std::io::{self, BufRead, BufReader};
use std::path::Path;

mod capability;
pub mod checker;
pub mod convert;
#[cfg(feature = "diagnostics")]
pub mod diagnostics;
pub mod environment;
pub mod id;
mod indexed_prop;
mod inductive;
pub mod judgment;
pub mod level;
pub mod machine;
pub mod mgso;
pub mod nat;
pub mod observation;
pub mod parser;
pub mod receipt;
pub mod receipt_store;
#[cfg(feature = "semantic-witness")]
pub mod semantic_witness;
pub mod syntax;
pub mod typecheck;
pub mod value;
pub mod verdict;

use checker::{Limits, check_export};
pub use observation::CheckedDecl;
use parser::parse;
use verdict::Verdict;

/// Check one Arena export stream.
///
pub fn run<R: BufRead>(reader: R) -> Verdict {
    match parse(reader).and_then(|export| export.resolve()) {
        Ok(export) => check_export(export, Limits::default()),
        Err(error) => {
            if std::env::var_os("NUCLEUS_TRACE_PARSE_ERROR").is_some() {
                eprintln!("NUCLEUS_PARSE_ERROR: {error}");
            }
            Verdict::Error
        }
    }
}

/// Observe exact source bytes and completed declaration admissions.
///
/// This interface never reads a receipt and cannot bypass the independent
/// checker. Even after successful prefix checks, UNKNOWN/REJECT/ERROR produce
/// no verified-declaration candidates.
pub fn run_observed<R: BufRead>(reader: R) -> (Verdict, [u8; 32], Vec<CheckedDecl>) {
    run_observed_callback(reader, &mut |_| {})
}

/// A single callback path serves the ordinary MGSO observer and optional
/// read-witness collector. Only the Rust checker decides any verdict.
fn run_observed_callback<R: BufRead>(
    reader: R,
    callback: &mut dyn FnMut(&CheckedDecl),
) -> (Verdict, [u8; 32], Vec<CheckedDecl>) {
    let mut hashed = BufReader::new(observation::Sha256Read::new(reader));
    let parsed = parse(&mut hashed).and_then(|export| export.resolve());
    // On early parse errors, finish hashing the entire supplied source rather
    // than silently recording a digest of only the parser-consumed prefix.
    let complete = io::copy(&mut hashed, &mut io::sink()).is_ok();
    let source_sha256 = hashed.into_inner().finish();
    let mut checked = Vec::new();
    let verdict = match parsed {
        Ok(export) => checker::check_export_observed(export, Limits::default(), &mut |event| {
            callback(&event);
            checked.push(event);
        }),
        Err(error) => {
            if std::env::var_os("NUCLEUS_TRACE_PARSE_ERROR").is_some() {
                eprintln!("NUCLEUS_PARSE_ERROR: {error}");
            }
            Verdict::Error
        }
    };
    let verdict = if complete { verdict } else { Verdict::Error };
    if verdict != Verdict::Accept {
        checked.clear();
    }
    (verdict, source_sha256, checked)
}

/// Observe source-bound, *partial* actual kernel environment reads.
///
/// The returned whole-export digest is a mandatory conservative global
/// invalidation barrier, including guards that depend on later declarations.
/// No local read set is certified complete; never promote a stored witness to
/// a kernel ACCEPT or use it to skip proof checking.
#[cfg(feature = "semantic-witness")]
pub fn run_dependency_witness<R: BufRead>(
    reader: R,
) -> (Verdict, [u8; 32], Vec<semantic_witness::ObservedSemanticWitness>) {
    let scope = semantic_witness::ReadScope::enter();
    let mut provisional = Vec::new();
    let (verdict, source_sha256, _) = run_observed_callback(reader, &mut |event| {
        provisional.push((event.clone(), scope.drain()));
    });
    if verdict != Verdict::Accept {
        // An earlier admitted prefix is not evidence for a failed export.
        return (verdict, source_sha256, Vec::new());
    }
    let observed = provisional.into_iter().map(|(declaration, constant_reads)| {
        semantic_witness::ObservedSemanticWitness {
            declaration,
            global_export_sha256: source_sha256,
            constant_reads,
            read_coverage: "PARTIAL",
            verification_reuse_authority: "NONE",
            proof_skips: 0,
        }
    }).collect();
    (verdict, source_sha256, observed)
}

/// Run the full independent checker, then compare/write optional MGSO shadow
/// candidates. No cached object can supply or change the returned verdict.
pub fn run_shadow<R: BufRead>(
    reader: R,
    store_dir: &Path,
    verifier_build_id: &str,
    config: &receipt::VerificationConfig,
) -> Verdict {
    use receipt::{ExportIdentity, RootManifest, build_receipts};
    use receipt_store::{ReceiptStore, ShadowResult};

    let (verdict, source_sha256, checked) = run_observed(reader);
    let identity = ExportIdentity {
        export_sha256: source_sha256.iter().map(|byte| format!("{byte:02x}")).collect(),
        export_format: config.export_format.clone(),
        verifier_build_id: verifier_build_id.to_string(),
        verification_config_sha256: config.sha256(),
    };
    if let Err(error) = identity.validate() {
        eprintln!("NUCLEUS_MGSO_SHADOW:status=unknown;reason={error};authority=none");
        return verdict;
    }
    let store = ReceiptStore::new(store_dir.to_path_buf());
    let shadow = store.read_shadow(&identity);
    match &shadow {
        ShadowResult::CandidateMatch { declarations, .. } if verdict == Verdict::Accept => {
            eprintln!("NUCLEUS_MGSO_SHADOW:status=candidate-match;declarations={declarations};authority=none;fresh-check=true");
        }
        ShadowResult::CandidateMatch { .. } => {
            eprintln!("NUCLEUS_MGSO_SHADOW:status=unknown;reason=stale-candidate-disagrees-with-fresh-check;authority=none");
        }
        ShadowResult::Stale(reason) => {
            eprintln!("NUCLEUS_MGSO_SHADOW:status=stale;reason={reason};authority=none");
        }
        ShadowResult::Unknown(reason) => {
            eprintln!("NUCLEUS_MGSO_SHADOW:status=unknown;reason={reason};authority=none");
        }
    }

    if verdict == Verdict::Accept && !checked.is_empty() {
        let write: Result<(), String> = (|| {
            let objects = build_receipts(&checked, &identity).map_err(|err| err.to_string())?;
            let root = RootManifest::from_receipts(&identity, &objects).map_err(|err| err.to_string())?;
            store.write_accepted(&objects, &root).map_err(|err| err.to_string())
        })();
        // Storage failure is diagnostic, never a change to kernel judgment.
        match write {
            Ok(()) => eprintln!("NUCLEUS_MGSO_SHADOW:write=complete;declarations={};authority=none", checked.len()),
            Err(error) => eprintln!("NUCLEUS_MGSO_SHADOW:write=unknown;reason={error};authority=none"),
        }
    }
    verdict
}

/// Inspect a stored candidate after independently hashing the exact current
/// source bytes, without parsing or checking a theorem.
///
/// This is strictly a transport/integrity operation. Even a matching root
/// proves nothing by itself: its alleged prior kernel verdict must be
/// authenticated through an independent trusted provenance boundary, and the
/// command-line interface always returns UNKNOWN rather than ACCEPT.
pub fn inspect_shadow<R: io::Read>(
    reader: R,
    store_dir: &Path,
    verifier_build_id: &str,
    config: &receipt::VerificationConfig,
) -> receipt_store::ShadowResult {
    use receipt::ExportIdentity;
    use receipt_store::{ReceiptStore, ShadowResult};

    let mut hashed = observation::Sha256Read::new(reader);
    if let Err(error) = io::copy(&mut hashed, &mut io::sink()) {
        return ShadowResult::Unknown(format!("source-byte-measurement-failed:{error}"));
    }
    let source_sha256 = hashed.finish();
    let identity = ExportIdentity {
        export_sha256: source_sha256.iter().map(|byte| format!("{byte:02x}")).collect(),
        export_format: config.export_format.clone(),
        verifier_build_id: verifier_build_id.to_string(),
        verification_config_sha256: config.sha256(),
    };
    if let Err(error) = identity.validate() {
        return ShadowResult::Unknown(format!("invalid-inspection-identity:{error}"));
    }
    ReceiptStore::new(store_dir.to_path_buf()).read_shadow(&identity)
}

/// Run with deterministic operation counters. The feature is diagnostic-only:
/// the verdict is produced by the same checker entry point as a normal build.
#[cfg(feature = "diagnostics")]
pub fn run_with_diagnostics<R: BufRead>(reader: R) -> diagnostics::DiagnosticRun {
    diagnostics::reset();
    let verdict = run(reader);
    diagnostics::DiagnosticRun {
        verdict,
        operations: diagnostics::snapshot(),
    }
}
