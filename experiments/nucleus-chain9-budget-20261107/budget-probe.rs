//! Runs the native checker with an explicit diagnostic judgment allowance.
use std::io::{self, BufReader};
use std::process::ExitCode;

fn main() -> ExitCode {
    let Some(steps) = std::env::args().nth(1).and_then(|arg| arg.parse::<usize>().ok())
    else { return ExitCode::from(3); };
    if !matches!(steps, 262_144 | 524_288 | 1_048_576) {
        return ExitCode::from(3);
    }
    match std::thread::Builder::new().stack_size(64 * 1024 * 1024).spawn(move || {
        use metatron_kernel::{checker, parser};
        let reader = BufReader::new(io::stdin().lock());
        match parser::parse(reader).and_then(|export| export.resolve()) {
            Ok(export) => checker::check_export(export, checker::Limits {
                judgment_steps: steps
            }).exit_code() as u8,
            Err(error) => {
                eprintln!("{error}");
                3
            }
        }
    }) {
        Ok(worker) => ExitCode::from(worker.join().unwrap_or(3)),
        Err(_) => ExitCode::from(3),
    }
}
