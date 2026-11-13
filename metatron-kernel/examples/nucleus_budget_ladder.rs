//! Research-only budget sensitivity wrapper around the *same* native checker.
//! No source, evaluator, recursor, cache, or fuel semantics are changed.
//! Requires `cargo build --locked --features diagnostics --example nucleus_budget_ladder`.

use std::io::{self,BufReader};
use std::process::ExitCode;

use metatron_kernel::checker::{check_export,Limits};
use metatron_kernel::parser::parse;
use metatron_kernel::verdict::Verdict;

fn main()->ExitCode {
    let mut args=std::env::args().skip(1);
    let Some(arg)=args.next() else {return ExitCode::from(3)};
    let Ok(steps)=arg.parse::<usize>() else {return ExitCode::from(3)};
    // Historical C45 n7 constructor threshold; diagnostic only, not Arena admission.
    if args.next().is_some() || ![
        65_536, 131_072, 262_144, 524_288,
        1_048_576, 2_097_152, 4_194_304, 8_388_608,
        14_155_776,
    ].contains(&steps) {
        return ExitCode::from(3);
    }
    std::thread::Builder::new().name("nucleus-checker".into())
        .stack_size(64*1024*1024)
        .spawn(move||check_input(steps))
        .ok().and_then(|handle|handle.join().ok()).unwrap_or(ExitCode::from(3))
}

fn check_input(steps:usize)->ExitCode {
    let verdict=match parse(BufReader::new(io::stdin().lock()))
        .and_then(|export|export.resolve()) {
        Ok(source)=>check_export(source,Limits{judgment_steps:steps}),
        Err(_)=>Verdict::Error,
    };
    eprintln!("C107_BUDGET:steps={steps}:verdict={verdict:?}");
    ExitCode::from(verdict.exit_code() as u8)
}
