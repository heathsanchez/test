use std::io::{self, BufReader};
use std::process::ExitCode;

fn main() -> ExitCode {
    // Exported binding DAGs can be deep even when inference is shared.
    // Make the checker stack explicit instead of depending on the launcher.
    match std::thread::Builder::new()
        .name("nucleus-checker".into())
        .stack_size(64 * 1024 * 1024)
        .spawn(check_input)
    {
        Ok(worker) => worker.join().unwrap_or(ExitCode::from(3)),
        Err(_) => ExitCode::from(3),
    }
}

fn check_input() -> ExitCode {
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
