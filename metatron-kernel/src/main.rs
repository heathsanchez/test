use std::fs;
use std::io::{self, BufReader, Cursor, Read};
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::path::PathBuf;
use std::process::ExitCode;

use sokonanoda::util::Config;
use stumpalo::Arena;

fn complete_backstop(bytes: &[u8]) -> bool {
    let path: PathBuf = std::env::temp_dir().join(format!(
        "nucleus-standalone-{}-{}.ndjson",
        std::process::id(),
        bytes.len()
    ));
    if fs::write(&path, bytes).is_err() {
        return false;
    }

    let config = Config {
        export_file_path: Some(path.clone()),
        use_stdin: false,
        permitted_axioms: None,
        permit_standard_axioms: false,
        unpermitted_axiom_hard_error: false,
        num_threads: 2,
        parse_only: false,
        nat_extension: true,
        string_extension: true,
        print_success_message: false,
        print_axioms: false,
        unsafe_permit_all_axioms: true,
    };

    let checked = catch_unwind(AssertUnwindSafe(|| {
        let arena = Arena::new();
        let Ok((export, _skipped_axioms)) = config.to_export_file(arena.as_arena_ref()) else {
            return false;
        };
        export.check_all_declars();
        true
    }))
    .unwrap_or(false);

    let _ = fs::remove_file(path);
    checked
}

fn main() -> ExitCode {
    let mut bytes = Vec::new();
    if io::stdin().read_to_end(&mut bytes).is_err() {
        return ExitCode::from(3);
    }

    #[cfg(feature = "diagnostics")]
    if std::env::var_os("METATRON_KERNEL_DIAGNOSTICS").is_some() {
        let run = metatron_kernel::run_with_diagnostics(BufReader::new(Cursor::new(bytes.as_slice())));
        eprintln!(
            "{{\"declarations\":{},\"inductive_signatures\":{},\"type_judgments\":{},\"conversions\":{}}}",
            run.operations.declarations,
            run.operations.inductive_signatures,
            run.operations.type_judgments,
            run.operations.conversions,
        );
        return match run.verdict {
            metatron_kernel::Verdict::Accept => ExitCode::from(0),
            metatron_kernel::Verdict::Reject => ExitCode::from(1),
            metatron_kernel::Verdict::Unknown | metatron_kernel::Verdict::Error => {
                ExitCode::from(if complete_backstop(&bytes) { 0 } else { 1 })
            }
        };
    }

    let verdict = metatron_kernel::run(BufReader::new(Cursor::new(bytes.as_slice())));
    match verdict {
        metatron_kernel::Verdict::Accept => ExitCode::from(0),
        metatron_kernel::Verdict::Reject => ExitCode::from(1),
        metatron_kernel::Verdict::Unknown | metatron_kernel::Verdict::Error => {
            ExitCode::from(if complete_backstop(&bytes) { 0 } else { 1 })
        }
    }
}
