use std::io::{self, BufReader};
use std::process::ExitCode;

fn main() -> ExitCode {
    // Exported binding DAGs can be deep even when inference is shared. Keep
    // the checker stack independent of the launcher's platform default.
    // C238: observation-only bounded stack A/B. Default remains 64 MiB.
    // Increasing stack cannot turn an unproved typing judgment into a proof;
    // source inputs, checker rules, and step budget are unchanged.
    let worker_stack_mib = std::env::var("NUCLEUS_C238_STACK_MIB").ok()
        .and_then(|value| value.parse::<usize>().ok())
        .filter(|value| matches!(value, 64 | 128 | 256))
        .unwrap_or(64);
    match std::thread::Builder::new()
        .name("nucleus-checker".into())
        .stack_size(worker_stack_mib * 1024 * 1024)
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
