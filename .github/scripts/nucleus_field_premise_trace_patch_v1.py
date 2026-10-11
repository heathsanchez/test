#!/usr/bin/env python3
"""Pure diagnostic trace of source-certified field-application premise failures.

Input: Rust checker after contextual patch and field-application patch.
Only inserts bounded diagnostic tracing at existing false returns. No semantic
candidate is promoted and no generic failed premise is silently accepted.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel")/"src/typecheck.rs"
s=p.read_text()
begin=s.index("    pub(crate) fn checked_field_application_congruence(")
end=s.index("    pub fn convert(&self, left: &TypeValue",begin)
piece=s[begin:end]
N=piece.count("return false")
assert N>=10 and N<=22,N
parts=piece.split("return false")
translated=parts[0]
for i,rest in enumerate(parts[1:],start=1):
    translated+=f"return trace_first_failed_field_premise({i})"+rest
key="    ) -> bool {\n"
assert translated.count(key)>=1
helper=r'''        #[track_caller]
        fn trace_first_failed_field_premise(stage: usize) -> bool {
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_FIELD_APP_FIRST_FAIL").is_some() {
                thread_local! {
                    static COUNTS: std::cell::RefCell<[usize;32]> =
                        const { std::cell::RefCell::new([0;32]) };
                }
                COUNTS.with(|cell| {
                    let mut counts=cell.borrow_mut();
                    if stage < counts.len() {
                        counts[stage]+=1;
                        if counts[stage]<=8 {
                            eprintln!(
                                "NUCLEUS_FIELD_APP_FIRST_FAIL:stage={stage}:occurrence={}",
                                counts[stage],
                            );
                        }
                    }
                });
            }
            false
        }

'''
translated=translated.replace(key,key+helper,1)
s=s[:begin]+translated+s[end:]
p.write_text(s)
print("NUCLEUS_FIELD_APP_FIRST_FAILURE_STAGE_COUNT",N)
