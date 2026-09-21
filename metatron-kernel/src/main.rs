use std::io::{self, BufReader};
use std::process::ExitCode;

fn main() -> ExitCode {
    #[cfg(feature = "diagnostics")]
    if std::env::var_os("METATRON_KERNEL_DIAGNOSTICS").is_some() {
        let run = metatron_kernel::run_with_diagnostics(BufReader::new(io::stdin().lock()));
        eprintln!(
            "{{\"declarations\":{},\"inductive_signatures\":{},\"type_judgments\":{},\"conversions\":{}}}",
            run.operations.declarations,
            run.operations.inductive_signatures,
            run.operations.type_judgments,
            run.operations.conversions,
        );
        return ExitCode::from(run.verdict.exit_code() as u8);
    }
    let verdict = metatron_kernel::run(BufReader::new(io::stdin().lock()));
    ExitCode::from(verdict.exit_code() as u8)
}
