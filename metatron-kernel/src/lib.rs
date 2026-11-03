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
    let mut hashed = BufReader::new(observation::Sha256Read::new(reader));
    let parsed = parse(&mut hashed).and_then(|export| export.resolve());
    // On early parse errors, finish hashing the entire supplied source rather
    // than silently recording a digest of only the parser-consumed prefix.
    let complete = io::copy(&mut hashed, &mut io::sink()).is_ok();
    let source_sha256 = hashed.into_inner().finish();
    let mut checked = Vec::new();
    let verdict = match parsed {
        Ok(export) => checker::check_export_observed(export, Limits::default(), &mut |event| {
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
