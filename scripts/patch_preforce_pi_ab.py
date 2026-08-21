from pathlib import Path
import os

mode=os.environ['MG_AB_MODE']
conv=Path('kernel/src/conv.rs')
s=conv.read_text()

old='''    #[inline]\n    fn unify<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        let x = self.force_thunk(depth, x);\n        let y = self.force_thunk(depth, y);\n        if std::ptr::eq(x, y) {\n            return true;\n        }\n        self.unify_general::<RIGID>(depth, x, y)\n    }'''
if mode in ('preptr','combined'):
    new='''    #[inline]\n    fn unify<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        if std::ptr::eq(x, y) {\n            return true;\n        }\n        let x = self.force_thunk(depth, x);\n        let y = self.force_thunk(depth, y);\n        if std::ptr::eq(x, y) {\n            return true;\n        }\n        self.unify_general::<RIGID>(depth, x, y)\n    }'''
    if old not in s: raise SystemExit('unify anchor missing')
    s=s.replace(old,new,1)

oldpi='''                if !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                let dx = *dx;'''
if mode in ('pidomain','combined'):
    newpi='''                if !std::ptr::eq(*dx, *dy) && !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                let dx = *dx;'''
    if oldpi not in s: raise SystemExit('Pi domain anchor missing')
    s=s.replace(oldpi,newpi,1)

conv.write_text(s)
print('patched',mode)
