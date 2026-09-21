use std::io::{self, BufReader};
use std::process::ExitCode;

fn main() -> ExitCode {
    let verdict = metatron_kernel::run(BufReader::new(io::stdin().lock()));
    ExitCode::from(verdict.exit_code() as u8)
}
