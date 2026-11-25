//! Whole-export admission for one closed, nonrecursive nullary inductive family.
//! Not a general 3.2 typechecker. Reconstruct the actual dependent eliminator
//! and every computation rule from the family; compare exact syntax modulo
//! binder names/implicitness. No reduction, proof irrelevance, reference
//! verdicts, test names, or legacy-format translation are used.
//! Any unhandled declaration or unsupported shape prevents ACCEPT.
use serde_json::Value;
use std::collections::HashSet;
use super::Features;

pub(super) const MAX_RECORDS: usize = 4096;

#[derive(Clone, Debug)]
enum Level { Zero, Succ(usize), Param(usize) }
#[derive(Clone, Debug)]
enum Expr {
    BVar(usize), Sort(usize), Const(usize, Vec<usize>),
    App(usize, usize), Pi(usize, usize), Lam(usize, usize),
}
struct Tables {
    names: Vec<Option<(usize,String)>>,
    name_keys: HashSet<(usize,String)>,
    levels: Vec<Level>,
    exprs: Vec<Expr>,
}
fn keys(x:&Value, expected:&[&str])->bool {
    x.as_object().is_some_and(|obj| obj.len()==expected.len() &&
        expected.iter().all(|k| obj.contains_key(*k)))
}
fn nat(x:&Value)->Option<usize> {
    usize::try_from(x.as_u64()?).ok()
}
fn num(x:&Value,k:&str)->Option<usize>{nat(x.get(k)?)}
fn boolean(x:&Value,k:&str)->Option<bool>{x.get(k)?.as_bool()}
fn arr<'a>(x:&'a Value,k:&str)->Option<&'a [Value]>{Some(x.get(k)?.as_array()?.as_slice())}
fn numbers(x:&Value,k:&str)->Option<Vec<usize>>{arr(x,k)?.iter().map(nat).collect()}
fn need(ok:bool)->Option<()> { ok.then_some(()) }

impl Tables {
    fn new()->Self { Self{names:vec![None],name_keys:HashSet::new(),levels:vec![Level::Zero],exprs:vec![]} }
    fn valid_name(&self,n:usize)->bool {n>0 && n<self.names.len()}
    fn name(&self,n:usize,p:usize,s:&str)->bool {
        self.names.get(n).and_then(Option::as_ref).is_some_and(|(pre,str)|*pre==p&&str==s)
    }
    fn add(&mut self,row:&Value)->Option<()> {
        if keys(row,&["in","str"]) {
            need(num(row,"in")?==self.names.len())?;
            let x=row.get("str")?;
            need(keys(x,&["pre","str"]))?;
            let pre=num(x,"pre")?;
            need(pre<self.names.len())?;
            let key=(pre,x.get("str")?.as_str()?.to_owned());
            need(self.name_keys.insert(key.clone()))?;
            self.names.push(Some(key));
            return Some(());
        }
        if keys(row,&["il","succ"]) {
            let x=num(row,"succ")?;
            need(num(row,"il")?==self.levels.len()&&x<self.levels.len())?;
            self.levels.push(Level::Succ(x));
            return Some(());
        }
        if keys(row,&["il","param"]) {
            let x=num(row,"param")?;
            need(num(row,"il")?==self.levels.len()&&self.valid_name(x))?;
            self.levels.push(Level::Param(x));
            return Some(());
        }
        let id=num(row,"ie")?;
        need(id==self.exprs.len())?;
        let e=if keys(row,&["ie","sort"]) {
            let l=num(row,"sort")?; need(l<self.levels.len())?; Expr::Sort(l)
        } else if keys(row,&["ie","bvar"]) {
            Expr::BVar(num(row,"bvar")?)
        } else if keys(row,&["ie","const"]) {
            let c=row.get("const")?;
            need(keys(c,&["name","us"]))?;
            let n=num(c,"name")?; let us=numbers(c,"us")?;
            need(self.valid_name(n)&&us.iter().all(|&l|l<self.levels.len()))?;
            Expr::Const(n,us)
        } else if keys(row,&["ie","app"]) {
            let c=row.get("app")?; need(keys(c,&["fn","arg"]))?;
            let f=num(c,"fn")?; let a=num(c,"arg")?; need(f<id&&a<id)?;
            Expr::App(f,a)
        } else if keys(row,&["ie","forallE"]) || keys(row,&["ie","lam"]) {
            let is_pi=row.get("forallE").is_some();
            let c=row.get(if is_pi {"forallE"} else {"lam"})?;
            need(keys(c,&["binderInfo","body","name","type"]))?;
            need(num(c,"name")?<self.names.len())?;
            need(matches!(c.get("binderInfo")?.as_str()?,
                "default"|"implicit"|"strictImplicit"|"instImplicit"))?;
            let d=num(c,"type")?;let b=num(c,"body")?;need(d<id&&b<id)?;
            if is_pi {Expr::Pi(d,b)} else {Expr::Lam(d,b)}
        } else { return None; };
        self.exprs.push(e);
        Some(())
    }
    fn constant(&self,e:usize,name:usize)->bool {
        matches!(self.exprs.get(e),Some(Expr::Const(n,ls)) if *n==name&&ls.is_empty())
    }
    fn variable(&self,e:usize,i:usize)->bool {
        matches!(self.exprs.get(e),Some(Expr::BVar(n)) if *n==i)
    }
    fn app_of(&self,e:usize,i:usize,arg:impl FnOnce(usize)->bool)->bool {
        matches!(self.exprs.get(e),Some(Expr::App(f,a)) if self.variable(*f,i)&&arg(*a))
    }
    fn binder(&self,e:usize,pi:bool)->Option<(usize,usize)> {
        match (pi,self.exprs.get(e)?) {
            (true,Expr::Pi(d,b)) | (false,Expr::Lam(d,b)) => Some((*d,*b)), _=>None,
        }
    }
    fn closed_level(&self,mut l:usize)->Option<usize> {
        let mut n=0usize;
        loop { match *self.levels.get(l)? {
            Level::Zero=>return Some(n),
            Level::Succ(x)=>{need(x<l)?; n=n.checked_add(1)?;l=x;},
            Level::Param(_)=>return None,
        }}
    }
    fn sort_of(&self,e:usize)->Option<usize> {
        if let Expr::Sort(l)=self.exprs.get(e)? {Some(*l)} else {None}
    }
    fn motive_level(&self,e:usize,param:Option<usize>)->bool {
        let Some(l)=self.sort_of(e) else{return false;};
        match param {
            None=>matches!(self.levels.get(l),Some(Level::Zero)),
            Some(p)=>matches!(self.levels.get(l),Some(Level::Param(n)) if *n==p),
        }
    }
    // Independently derive the common telescope:
    // (motive : I -> Sort v) (minor_j : motive ctor_j), with
    // motive at de Bruijn index j when opening the j-th minor binder.
    fn motive_and_minors(&self,e:usize,pi:bool,family:usize,ctors:&[usize],param:Option<usize>)->Option<usize> {
        let (domain,mut body)=self.binder(e,pi)?;
        let (d,c)=self.binder(domain,true)?;
        need(self.constant(d,family)&&self.motive_level(c,param))?;
        for (j,&ctor) in ctors.iter().enumerate() {
            let (d,b)=self.binder(body,pi)?;
            need(self.app_of(d,j,|arg|self.constant(arg,ctor)))?;
            body=b;
        }
        Some(body)
    }
    fn block(&self,block:&Value)->Option<()> {
        need(keys(block,&["types","ctors","recs"]))?;
        let types=arr(block,"types")?;let constructors=arr(block,"ctors")?;let recs=arr(block,"recs")?;
        need(types.len()==1&&recs.len()==1&&constructors.len()<=64)?;
        let t=&types[0];let r=&recs[0];
        need(keys(t,&["all","ctors","hasEta","hasLargeElim","hasProjections",
            "isImpredicative","isK","isRec","isUnsafe","levelParams","name",
            "numIndices","numNested","numParams","type"]))?;
        need(keys(r,&["all","isUnsafe","k","levelParams","name","numIndices",
            "numMinors","numMotives","numParams","rules","type"]))?;
        let i=num(t,"name")?;let rec=num(r,"name")?;
        let ctors=numbers(t,"ctors")?;let n=ctors.len();
        need(n==constructors.len()&&self.valid_name(i)&&self.valid_name(rec)&&self.name(rec,i,"rec"))?;
        let mut declared=HashSet::from([i,rec]);
        need(declared.len()==2&&ctors.iter().all(|&x|self.valid_name(x)&&declared.insert(x)))?;
        need(numbers(t,"all")?==[i]&&numbers(t,"levelParams")?.is_empty())?;
        need(num(t,"numIndices")?==0&&num(t,"numNested")?==0&&num(t,"numParams")?==0&&
            !boolean(t,"isRec")?&&!boolean(t,"isUnsafe")?)?;
        let f=Features::read(t).ok()?;
        let lev=self.closed_level(self.sort_of(num(t,"type")?)?)?;
        need(!f.imp||lev==0)?;
        need(!f.projections||(n==1&&!f.imp))?;
        need(!f.eta||f.projections)?;
        need(!f.k||(n==1&&lev==0))?;
        need(!f.large||(!f.imp&&(lev>0||n==0||(n==1&&(f.eta||f.k)))))?;
        for (j,c) in constructors.iter().enumerate() {
            need(keys(c,&["cidx","induct","isUnsafe","levelParams","name","numFields","numParams","type"]))?;
            need(num(c,"name")?==ctors[j]&&num(c,"induct")?==i&&num(c,"cidx")?==j&&
                num(c,"numFields")?==0&&num(c,"numParams")?==0&&!boolean(c,"isUnsafe")?&&
                numbers(c,"levelParams")?.is_empty()&&self.constant(num(c,"type")?,i))?;
        }
        need(numbers(r,"all")?==[i]&&!boolean(r,"isUnsafe")?&&boolean(r,"k")?==f.k&&
            num(r,"numIndices")?==0&&num(r,"numParams")?==0&&num(r,"numMinors")?==n&&num(r,"numMotives")?==1)?;
        let ps=numbers(r,"levelParams")?;
        let param=if f.large {
            need(ps.len()==1&&self.valid_name(ps[0])&&self.name(ps[0],0,"u"))?;
            Some(ps[0])
        } else {need(ps.is_empty())?;None};
        let major=self.motive_and_minors(num(r,"type")?,true,i,&ctors,param)?;
        let (major_ty,result)=self.binder(major,true)?;
        need(self.constant(major_ty,i)&&self.app_of(result,n+1,|a|self.variable(a,0)))?;
        let rules=arr(r,"rules")?;
        need(rules.len()==if f.large {n}else{0})?;
        for (j,rule) in rules.iter().enumerate() {
            need(keys(rule,&["ctor","nfields","rhs"]))?;
            need(num(rule,"ctor")?==ctors[j]&&num(rule,"nfields")?==0)?;
            let rhs=self.motive_and_minors(num(rule,"rhs")?,false,i,&ctors,param)?;
            need(self.variable(rhs,n-1-j))?;
        }
        Some(())
    }
}

pub(super) fn admits(rows:&[Value])->bool {
    // The final, unique declaration must be the fully checked block.
    // An extra definition, theorem, axiom or other declaration cannot be
    // admitted by this fragment, even after a valid inductive declaration.
    fn check(rows:&[Value])->Option<()> {
        let (block,tables)=rows.split_last()?;
        need(keys(block,&["inductive"]))?;
        let mut t=Tables::new();
        for row in tables { t.add(row)?; }
        t.block(block.get("inductive")?)
    }
    rows.len()<=MAX_RECORDS&&check(rows).is_some()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn no_unchecked_declarations_or_empty_exports() {
        assert!(!admits(&[]));
        assert!(!admits(&[serde_json::json!({"axiom":{}})]));
        assert!(!admits(&[serde_json::json!({"inductive":{"types":[],"ctors":[],"recs":[]}})]));
    }
    #[test]
    fn structural_name_and_expression_integrity() {
        let mut t=Tables::new();
        assert!(t.add(&serde_json::json!({"in":1,"str":{"pre":0,"str":"I"}})).is_some());
        assert!(t.add(&serde_json::json!({"in":2,"str":{"pre":0,"str":"I"}})).is_none());
        assert!(t.add(&serde_json::json!({"ie":0,"app":{"fn":0,"arg":0}})).is_none());
        assert!(t.add(&serde_json::json!({"ie":0,"const":{"name":2,"us":[]}})).is_none());
    }
}
