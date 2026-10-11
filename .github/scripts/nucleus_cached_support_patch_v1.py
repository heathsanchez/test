#!/usr/bin/env python3
"""Source-authored, immutable AST dependency-support memo.

Only cache completely traversed sets of free de Bruijn indices. This caches
an AST fact, never an equality, type, proof, UNKNOWN or resource exhaustion.
Applied after nucleus_contextual_capability_patch_v1.py.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel")
tc=root/"src/typecheck.rs"
t=tc.read_text()
anchor="""    pub(crate) contextual_conversion_memo: Rc<RefCell<HashMap<
        (crate::machine::AuthorityId, TypeValue, TypeValue, usize, Vec<TypeValue>, bool),
        crate::judgment::WarrantId,
    >>>,
"""
assert t.count(anchor)==1, f"typecheck memo field anchors {t.count(anchor)}"
t=t.replace(anchor,anchor+
"""    // Cache ONLY a complete immutable source AST free-variable support set.
    // Neither a resource-bound miss nor a conversion judgment is cached here.
    pub(crate) contextual_source_support: Rc<RefCell<HashMap<ExprId, Vec<u64>>>>,
""",1)
needle="""            contextual_conversion_memo: Rc::new(RefCell::new(HashMap::new())),
"""
assert t.count(needle)==5,t.count(needle)
t=t.replace(needle,needle+
"""            contextual_source_support: Rc::new(RefCell::new(HashMap::new())),
""")
tc.write_text(t)

cv=root/"src/convert.rs"
s=cv.read_text()
start=s.index("    let mut tasks = vec![(left.expr, 0_usize)];",s.index("fn checked_capture_support_congruence("))
end=s.index("    let mut certificate = Vec::with_capacity(indices.len());",start)
old=s[start:end]
# Preserve the exact original algorithm, including its strict budget guards.
# Only the completed sorted indices are eligible for retention.
def indent(src,spaces):
    return "".join(" "*spaces + line if line.strip() else line for line in src.splitlines(keepends=True))
inner=old.replace('    let mut fuel = budget.min(2048);\n', '')
assert inner != old, 'expected exact local traversal fuel declaration'
# Important: the existing code includes "let mut indices...;indices.sort_unstable();"
# and completely finishes before the conditional positive-cache insert.
assert "indices.sort_unstable();" in inner
new="""    let mut fuel = budget.min(2048);
    let cache_enabled = std::env::var_os("NUCLEUS_EXPERIMENTAL_SUPPORT_CACHE").is_some();
    let cached_indices = cache_enabled.then(|| {
        checker.contextual_source_support.borrow().get(&left.expr).cloned()
    }).flatten();
    let indices = if let Some(indices) = cached_indices {
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_SUPPORT_CACHE_HIT").is_some() {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static HIT:AtomicUsize=AtomicUsize::new(0);
            if HIT.fetch_add(1,Ordering::Relaxed)<96 {
                eprintln!("NUCLEUS_SUPPORT_CACHE_HIT:expr={:?}:support={}",left.expr,indices.len());
            }
        }
        indices
    } else {
"""+indent(inner,4)+"""        if cache_enabled {
            checker.contextual_source_support.borrow_mut().insert(
                left.expr,indices.clone(),
            );
        }
        indices
    };
"""
s=s[:start]+new+s[end:]
cv.write_text(s)
print("PATCHED_CERTIFIED_SUPPORT_CACHE_V1")
