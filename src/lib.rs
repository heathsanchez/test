use std::io::BufRead;

pub mod verdict;

use verdict::Verdict;

/// Check one Arena export stream.
///
/// G0 deliberately declines every readable stream until the parser and
/// semantic substrate earn stronger verdicts.
pub fn run<R: BufRead>(_reader: R) -> Verdict {
    Verdict::Unknown
}
