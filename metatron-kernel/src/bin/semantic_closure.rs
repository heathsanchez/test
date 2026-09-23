use std::ffi::OsStr;
use std::fs::File;
use std::io::{self, BufReader, Cursor, Read, Write};
use std::process::{Command, ExitCode, Stdio};

use metatron_kernel::verdict::Verdict;

fn exit(code: u8) -> ExitCode {
    ExitCode::from(code)
}

fn flash_command() -> Result<Command, ()> {
    let bin = std::env::var_os("NUCLEUS_FLASH_BIN").ok_or(())?;
    let config = std::env::var_os("NUCLEUS_FLASH_CONFIG").ok_or(())?;
    let mut command = Command::new(bin);
    command.arg(config);
    Ok(command)
}

fn flash_exit(status: std::process::ExitStatus) -> ExitCode {
    match status.code() {
        Some(0) => exit(0),
        Some(_) => exit(1),
        None => exit(3),
    }
}

fn fallback_file(path: &OsStr) -> ExitCode {
    let Ok(file) = File::open(path) else {
        return exit(3);
    };
    let Ok(mut command) = flash_command() else {
        return exit(3);
    };
    match command
        .stdin(Stdio::from(file))
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
    {
        Ok(status) => flash_exit(status),
        Err(_) => exit(3),
    }
}

fn fallback_bytes(bytes: &[u8]) -> ExitCode {
    let Ok(mut command) = flash_command() else {
        return exit(3);
    };
    let Ok(mut child) = command
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
    else {
        return exit(3);
    };
    let Some(mut stdin) = child.stdin.take() else {
        return exit(3);
    };
    if stdin.write_all(bytes).is_err() {
        return exit(3);
    }
    drop(stdin);
    match child.wait() {
        Ok(status) => flash_exit(status),
        Err(_) => exit(3),
    }
}

fn main() -> ExitCode {
    let mut args = std::env::args_os().skip(1);
    let input = args.next();
    if args.next().is_some() {
        return exit(3);
    }

    match input {
        Some(path) => {
            let Ok(file) = File::open(&path) else {
                return exit(3);
            };
            let verdict = metatron_kernel::run(BufReader::new(file));
            if verdict == Verdict::Accept {
                return exit(0);
            }
            fallback_file(&path)
        }
        None => {
            let mut bytes = Vec::new();
            if io::stdin().read_to_end(&mut bytes).is_err() {
                return exit(3);
            }
            let verdict = metatron_kernel::run(BufReader::new(Cursor::new(bytes.as_slice())));
            if verdict == Verdict::Accept {
                return exit(0);
            }
            fallback_bytes(&bytes)
        }
    }
}
