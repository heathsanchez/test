use std::io::{BufRead, Cursor, Read};

mod capability;
pub mod checker;
pub mod convert;
#[cfg(feature = "diagnostics")]
pub mod diagnostics;
pub mod environment;
pub mod id;
mod inductive;
mod indexed_prop;
mod renovation;
pub mod judgment;
pub mod level;
pub mod machine;
pub mod nat;
pub mod parser;
pub mod syntax;
pub mod typecheck;
pub mod value;
pub mod verdict;

use checker::{Limits, check_export};
use parser::parse;
use verdict::Verdict;

/// Check one Arena export stream.
///
pub fn run<R: BufRead>(mut reader: R) -> Verdict {
    let mut header = String::new();
    if reader.read_line(&mut header).is_err() {
        return Verdict::Error;
    }
    let version = serde_json::from_str::<serde_json::Value>(&header).ok()
        .and_then(|v| v.pointer("/meta/format/version").and_then(|x| x.as_str()).map(str::to_owned));
    if version.as_deref() == Some("3.2.0") {
        return match renovation::refute(reader) {
            Ok(Some(reason)) => {
                eprintln!("NUCLEUS_RENOVATION_REFUTATION: {reason}");
                Verdict::Reject
            }
            Ok(None) => Verdict::Unknown,
            Err(reason) => {
                eprintln!("NUCLEUS_RENOVATION_ERROR: {reason}");
                Verdict::Error
            }
        };
    }
    // The original 3.1 parser still receives the exact original byte stream,
    // including the original header and newline. Never relabel a 3.2 stream.
    let reader = Cursor::new(header.into_bytes()).chain(reader);
    match parse(reader).and_then(|export| export.resolve()) {
        Ok(export) => {
            // C225 diagnostic-only resource discrimination. A fresh checked
            // source export uses precisely the same kernel; the optional
            // increased budget is not the standard Arena/production policy.
            #[cfg(feature = "diagnostics")]
            let limits = std::env::var("NUCLEUS_C225_JUDGMENT_STEPS")
                .ok()
                .and_then(|n| n.parse::<usize>().ok())
                .filter(|n| (65_536..=69_632).contains(n))
                .map(|judgment_steps| Limits { judgment_steps })
                .unwrap_or_default();
            #[cfg(not(feature = "diagnostics"))]
            let limits = Limits::default();
            check_export(export, limits)
        },
        Err(error) => {
            if std::env::var_os("NUCLEUS_TRACE_PARSE_ERROR").is_some() {
                eprintln!("NUCLEUS_PARSE_ERROR: {error}");
            }
            Verdict::Error
        }
    }
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
