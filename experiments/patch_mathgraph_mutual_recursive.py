from pathlib import Path

p = Path("src/inductive.rs")
s = p.read_text()
old = '''                let is_recursive = {
                    let mut found = false;
                    'outer: for ctor_name in ind.all_ctor_names.iter() {
                        match self.declars.get(ctor_name).unwrap() {
                            Declar::Constructor(ctor_data @ ConstructorData { .. }) => {
                                let mut ctor_ty = ctor_data.info.ty;
                                while let Pi { binder_type, body, .. } = ctx.read_expr(ctor_ty) {
                                    if ctx.find_const(binder_type, |n| ind.all_ind_names.iter().any(|nn| n == *nn)) {
                                        found = true;
                                        break 'outer
                                    }
                                    ctor_ty = body;
                                }
                            }
                            _ => panic!(),
                        }
                    }
                    found
                };
'''
new = '''                let is_recursive = {
                    let mut found = false;
                    'outer: for ind_name in ind.all_ind_names.iter() {
                        let mutual = match self.declars.get(ind_name).unwrap() {
                            Declar::Inductive(mutual) => mutual,
                            _ => panic!(),
                        };
                        for ctor_name in mutual.all_ctor_names.iter() {
                            match self.declars.get(ctor_name).unwrap() {
                                Declar::Constructor(ctor_data @ ConstructorData { .. }) => {
                                    let mut ctor_ty = ctor_data.info.ty;
                                    while let Pi { binder_type, body, .. } = ctx.read_expr(ctor_ty) {
                                        if ctx.find_const(binder_type, |n| ind.all_ind_names.iter().any(|nn| n == *nn)) {
                                            found = true;
                                            break 'outer
                                        }
                                        ctor_ty = body;
                                    }
                                }
                                _ => panic!(),
                            }
                        }
                    }
                    found
                };
'''
assert old in s, "expected MathGraph is_recursive block not found"
p.write_text(s.replace(old, new, 1))
print("patched MathGraph is_recursive to scan the full mutual block")
