#!/usr/bin/env python3
"""Independent empty-frame allocation experiment on each source-reuse arm."""
import difflib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-reuse-20261104'))
import tournament as core

original_materialize=core.materialize
def materialize(repo,out,table=False,facts=False):
    kernel=original_materialize(repo,out,table,facts)
    p=kernel/'src/value.rs';before=p.read_text()
    after=core.replace_once(before,'static NEXT_ENV_FRAME_ID: AtomicU64 = AtomicU64::new(1);',
        'static NEXT_ENV_FRAME_ID: AtomicU64 = AtomicU64::new(1);\nthread_local! { static SHARED_EMPTY_FRAME: Rc<EnvNode> = Rc::new(EnvNode::Empty); }')
    after=core.replace_once(after,'Self(Rc::new(EnvNode::Empty))','Self(SHARED_EMPTY_FRAME.with(Rc::clone))')
    p.write_text(after)
    with (out/'source.patch').open('a') as f:
        f.write(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/metatron-kernel/src/value.rs',tofile='b/metatron-kernel/src/value.rs')))
    with (kernel/'tests/machine.rs').open('a') as f:
        f.write('''
#[test]
fn shared_empty_frame_remains_empty_after_independent_extensions() {
    use metatron_kernel::value::{EnvFrame,FreeId};
    let a=EnvFrame::empty();let b=EnvFrame::empty();
    let x=a.extend_free(FreeId(77));let y=b.extend_free(FreeId(88));
    assert_eq!(a.id(),0);assert_eq!(b.id(),0);
    assert!(a.lookup(0).is_none());assert!(b.lookup(0).is_none());
    assert_ne!(x.id(),y.id());
    assert!(matches!(x.lookup(0),Some(metatron_kernel::value::EnvBinding::Free(FreeId(77)))));
    assert!(matches!(y.lookup(0),Some(metatron_kernel::value::EnvBinding::Free(FreeId(88)))));
}
''')
    return kernel
core.materialize=materialize
if __name__=='__main__':core.main()
