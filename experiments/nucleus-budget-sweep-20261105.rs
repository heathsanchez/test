//! Research-only budget sweep. This binary is not part of the distributed checker.
//! All type judgments still pass through the exact source checker and normal
//! declarative limits. Only the number of available metered steps changes.

use std::io::{self, BufReader};
use std::process::ExitCode;

fn main() -> ExitCode {
    let Some(steps) = std::env::args().nth(1).and_then(|s| s.parse::<usize>().ok()) else {
        eprintln!("usage: nucleus-budget-sweep STEPS");
        return ExitCode::from(3);
    };
    let checker = || {
        let export = match metatron_kernel::parser::parse(BufReader::new(io::stdin().lock()))
            .and_then(|export| export.resolve())
        {
            Ok(export) => export,
            Err(error) => {
                eprintln!("source parse failed: {error}");
                return metatron_kernel::verdict::Verdict::Error;
            }
        };
        metatron_kernel::checker::check_export(
            export,
            metatron_kernel::checker::Limits { judgment_steps: steps },
        )
    };
    // Match the production binary's 64-MiB stack for large exported terms.
    match std::thread::Builder::new().stack_size(64 * 1024 * 1024).spawn(checker) {
        Ok(handle) => match handle.join() {
            Ok(verdict) => ExitCode::from(verdict.exit_code() as u8),
            Err(_) => ExitCode::from(3),
        },
        Err(_) => ExitCode::from(3),
    }
}
