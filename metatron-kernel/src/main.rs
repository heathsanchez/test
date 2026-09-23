use std::fs;
use std::io::{self, Read};
use std::panic::{AssertUnwindSafe, catch_unwind};
use std::path::PathBuf;
use std::process::ExitCode;

use sokonanoda::util::Config;
use stumpalo::Arena;

fn native_complete_check(bytes: &[u8]) -> bool {
    let path: PathBuf = std::env::temp_dir().join(format!(
        "nucleus-native-{}-{}.ndjson",
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
        return ExitCode::from(1);
    }
    ExitCode::from(if native_complete_check(&bytes) { 0 } else { 1 })
}
