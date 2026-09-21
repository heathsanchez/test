use std::io::BufRead;

pub mod checker;
pub mod convert;
pub mod environment;
pub mod id;
pub mod judgment;
pub mod level;
pub mod machine;
pub mod parser;
pub mod syntax;
pub mod typecheck;
pub mod value;
pub mod verdict;

use checker::{Limits, check_export};
use parser::parse;
use verdict::Verdict;

/// Check one Arena export stream.
///
pub fn run<R: BufRead>(reader: R) -> Verdict {
    match parse(reader).and_then(|export| export.resolve()) {
        Ok(export) => check_export(export, Limits::default()),
        Err(_) => Verdict::Error,
    }
}
