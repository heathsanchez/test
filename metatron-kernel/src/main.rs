use std::fs::File;
use std::io::{self, BufReader, Read};
use std::path::PathBuf;
use std::process::ExitCode;

use metatron_kernel::receipt::VerificationConfig;
use metatron_kernel::receipt_store::ShadowResult;
use sha2::{Digest, Sha256};

fn main() -> ExitCode {
    // Exported binding DAGs can be deep even when inference is shared. Keep
    // the checker stack independent of the launcher's platform default.
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
    let mut args = std::env::args_os().skip(1);
    match (args.next(), args.next(), args.next()) {
        (None, None, None) => {}
        (Some(flag), Some(directory), None)
            if flag == "--mgso-shadow-dir" || flag == "--mgso-inspect-dir" =>
        {
            let inspection_only = flag == "--mgso-inspect-dir";
            let build_id = match binary_build_id() {
                Ok(id) => id,
                Err(error) => {
                    eprintln!(
                        "NUCLEUS_MGSO_SHADOW:status=unknown;reason=build-id-unavailable:{error};authority=none"
                    );
                    if inspection_only {
                        // Inspection never falls through to a proof-checking
                        // verdict or claims a historical ACCEPT.
                        return ExitCode::from(2);
                    }
                    let verdict = metatron_kernel::run(BufReader::new(io::stdin().lock()));
                    return ExitCode::from(verdict.exit_code() as u8);
                }
            };
            let config = VerificationConfig {
                export_format: "3.1.0".to_string(),
                judgment_steps: 65_536,
                delta_policy: "GuardedSemanticFallback".to_string(),
                compiled_features: vec![
                    format!("os:{}", std::env::consts::OS),
                    format!("arch:{}", std::env::consts::ARCH),
                    format!("diagnostics:{}", cfg!(feature = "diagnostics")),
                ],
                nucleus_flags: std::env::vars_os()
                    .filter_map(|(key, value)| {
                        key.as_encoded_bytes()
                            .starts_with(b"NUCLEUS_")
                            .then(|| (raw_os_hex(&key), raw_os_hex(&value)))
                    })
                    .collect(),
            };
            if inspection_only {
                let result = metatron_kernel::inspect_shadow(
                    BufReader::new(io::stdin().lock()),
                    &PathBuf::from(directory),
                    &build_id,
                    &config,
                );
                match result {
                    ShadowResult::CandidateMatch { declarations, .. } => eprintln!(
                        "NUCLEUS_MGSO_INSPECT:status=candidate-match;authority=none;fresh-check=false;declarations={declarations}"
                    ),
                    ShadowResult::Stale(reason) => eprintln!(
                        "NUCLEUS_MGSO_INSPECT:status=stale;authority=none;fresh-check=false;reason={reason}"
                    ),
                    ShadowResult::Unknown(reason) => eprintln!(
                        "NUCLEUS_MGSO_INSPECT:status=unknown;authority=none;fresh-check=false;reason={reason}"
                    ),
                }
                return ExitCode::from(2);
            }
            let verdict = metatron_kernel::run_shadow(
                BufReader::new(io::stdin().lock()),
                &PathBuf::from(directory),
                &build_id,
                &config,
            );
            return ExitCode::from(verdict.exit_code() as u8);
        }
        _ => {
            eprintln!("Usage: metatron-kernel [--mgso-shadow-dir PATH|--mgso-inspect-dir PATH]");
            return ExitCode::from(3);
        }
    }
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

fn binary_build_id() -> io::Result<String> {
    let mut binary = File::open(std::env::current_exe()?)?;
    let mut digest = Sha256::new();
    let mut buffer = [0u8; 65536];
    loop {
        let bytes = binary.read(&mut buffer)?;
        if bytes == 0 {
            break;
        }
        digest.update(&buffer[..bytes]);
    }
    Ok(format!("binary-sha256:{:x}", digest.finalize()))
}

fn raw_os_hex(value: &std::ffi::OsStr) -> String {
    value
        .as_encoded_bytes()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}
