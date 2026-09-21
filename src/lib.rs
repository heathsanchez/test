use std::io::BufRead;

pub mod id;
pub mod parser;
pub mod syntax;
pub mod verdict;

use parser::parse;
use verdict::Verdict;

/// Check one Arena export stream.
///
/// G0 deliberately declines every readable stream until the parser and
/// semantic substrate earn stronger verdicts.
pub fn run<R: BufRead>(reader: R) -> Verdict {
    match parse(reader).and_then(|export| export.resolve()) {
        Ok(_) => Verdict::Unknown,
        Err(_) => Verdict::Error,
    }
}
