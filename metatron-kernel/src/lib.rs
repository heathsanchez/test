use std::io::BufRead;

mod capability;
pub mod checker;
pub mod convert;
#[cfg(feature = "diagnostics")]
pub mod diagnostics;
pub mod environment;
pub mod id;
mod inductive;
mod indexed_prop;
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
pub fn run<R: BufRead>(reader: R) -> Verdict {
    match parse(reader).and_then(|export| export.resolve()) {
        Ok(export) => {
            let mut limits = Limits::default();
            // Diagnostic-only finite budget sensitivity test; never active
            // in release builds without the explicit diagnostics feature.
            #[cfg(feature = "diagnostics")]
            if let Ok(raw) = std::env::var("NUCLEUS_DIAG_JUDGMENT_STEPS")
                && let Ok(requested) = raw.parse::<usize>()
                && (65_536..=524_288).contains(&requested)
            {
                limits.judgment_steps = requested;
                eprintln!("NUCLEUS_DIAG_JUDGMENT_STEPS={requested}");
            }
            #[cfg(not(feature = "diagnostics"))]
            let _ = &mut limits;
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
