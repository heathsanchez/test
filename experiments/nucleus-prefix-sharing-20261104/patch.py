from pathlib import Path
import re

def prefix_patch(s):
 s=s.replace('protected_prefix: Vec<TypeValue>','protected_prefix: ContextSpine')
 s=s.replace('    checked_binding_lineage: Rc<RefCell<HashMap<u64,Option<CheckedBinderWitness>>>>,','    context_arena: RefCell<ContextArena>,\n    checked_binding_lineage: Rc<RefCell<HashMap<u64,Option<CheckedBinderWitness>>>>,')
 s,n=re.subn(r'(checked_binding_lineage:\s*Rc::)',r'context_arena: RefCell::new(ContextArena::default()),\n            \1',s);assert n==5,n
 s=s.replace('protected_prefix:protected_context.to_vec()','protected_prefix:self.context_arena.borrow_mut().capture(protected_context)')
 s=s.replace('context.starts_with(&proof.protected_prefix)','proof.protected_prefix.is_prefix_of(context)')
 s=s.replace('recovered_context=record.protected_prefix;','recovered_context=record.protected_prefix.to_vec();').replace('recovered_context.starts_with(&record.protected_prefix)','record.protected_prefix.is_prefix_of(&recovered_context)')
 s+='\n'+(Path(__file__).resolve().parent/'prefix.rs').read_text()
 return s
