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
        (Some(flag), None, None) if flag == "--semantic-read-witness-v2" => {
            #[cfg(feature = "semantic-witness")]
            {
                use metatron_kernel::semantic_witness::{EnvironmentRead, TableRead};
                let (verdict, source_sha256, observed, global) =
                    metatron_kernel::run_dependency_witness_v2(BufReader::new(io::stdin().lock()));
                let identity = source_sha256.iter()
                    .map(|byte| format!("{byte:02x}"))
                    .collect::<String>();
                let tables = |reads: &[TableRead]| reads.iter().map(|read| serde_json::json!({
                    "table": read.table, "access": read.access,
                    "id": read.id, "present": read.present,
                })).collect::<Vec<_>>();
                let environment = |reads: &[EnvironmentRead]| reads.iter().map(|read| serde_json::json!({
                    "channel": read.channel, "name_id": read.name_id, "present": read.present,
                })).collect::<Vec<_>>();
                let declarations = observed.iter().map(|witness| serde_json::json!({
                    "index": witness.declaration.index,
                    "name": witness.declaration.name,
                    "kind": witness.declaration.kind,
                    "global_export_sha256": identity,
                    "constant_reads": witness.constant_reads.iter().map(|read| serde_json::json!({
                        "name_id": read.name_id, "present": read.present,
                    })).collect::<Vec<_>>(),
                    "table_reads": tables(&witness.table_reads),
                    "environment_reads": environment(&witness.environment_reads),
                    "read_coverage": "PARTIAL",
                    "verification_reuse_authority": "NONE",
                    "proof_skips": 0,
                })).collect::<Vec<_>>();
                let guards = global.guards.iter().map(|guard| serde_json::json!({
                    "stage": guard.stage, "result": guard.result,
                })).collect::<Vec<_>>();
                eprintln!("NUCLEUS_SEMANTIC_V2:{}", serde_json::json!({
                    "status": format!("{verdict:?}"),
                    "source_sha256": identity,
                    "global_barrier": "whole-export-sha256",
                    "read_coverage": global.read_coverage,
                    "semantic_dependency_completeness": "UNKNOWN",
                    "verification_reuse_authority": global.verification_reuse_authority,
                    "proof_skips": global.proof_skips,
                    "global": {
                        "source_resolution_reads": tables(&global.source_resolution_reads),
                        "preflight_reads": tables(&global.preflight_reads),
                        "guards": guards,
                    },
                    "declarations": declarations,
                }));
                return ExitCode::from(verdict.exit_code() as u8);
            }
            #[cfg(not(feature = "semantic-witness"))]
            {
                eprintln!("NUCLEUS_SEMANTIC_V2:status=unavailable;reason=feature-disabled;authority=none");
                return ExitCode::from(3);
            }
        }
        (Some(flag), None, None) if flag == "--semantic-read-witness" => {
            #[cfg(feature = "semantic-witness")]
            {
                let (verdict, source_sha256, observed) = metatron_kernel::run_dependency_witness(
                    BufReader::new(io::stdin().lock()),
                );
                let source_hex = source_sha256.iter()
                    .map(|byte| format!("{byte:02x}"))
                    .collect::<String>();
                for witness in &observed {
                    let reads = witness.constant_reads.iter().map(|read| {
                        serde_json::json!({"name_id": read.name_id, "present": read.present})
                    }).collect::<Vec<_>>();
                    eprintln!("NUCLEUS_SEMANTIC_READ:{}", serde_json::json!({
                        "index": witness.declaration.index,
                        "name": witness.declaration.name,
                        "kind": witness.declaration.kind,
                        "constant_reads": reads,
                        "global_export_sha256": source_hex,
                        "read_coverage": witness.read_coverage,
                        "verification_reuse_authority": witness.verification_reuse_authority,
                        "proof_skips": witness.proof_skips,
                    }));
                }
                eprintln!("NUCLEUS_SEMANTIC_SUMMARY:{}", serde_json::json!({
                    "status": format!("{verdict:?}"),
                    "source_sha256": source_hex,
                    "observed_declarations": observed.len(),
                    "read_coverage": "PARTIAL",
                    "global_barrier": "whole-export-sha256",
                    "verification_reuse_authority": "NONE",
                    "proof_skips": 0,
                }));
                return ExitCode::from(verdict.exit_code() as u8);
            }
            #[cfg(not(feature = "semantic-witness"))]
            {
                eprintln!("NUCLEUS_SEMANTIC_SUMMARY:status=unavailable;reason=feature-disabled;authority=none");
                return ExitCode::from(3);
            }
        }
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
            eprintln!("Usage: metatron-kernel [--mgso-shadow-dir PATH|--mgso-inspect-dir PATH|--semantic-read-witness|--semantic-read-witness-v2]");
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
