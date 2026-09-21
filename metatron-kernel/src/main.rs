use std::io;
use std::process::ExitCode;

fn main() -> ExitCode {
    let verdict = metatron_kernel::run(io::stdin().lock());
    ExitCode::from(verdict.exit_code() as u8)
}
