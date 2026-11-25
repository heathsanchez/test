//! Source-derived nonrecursive, nonindexed, single-family admission.
//! Validate parameter/field dependent typing in the Sort/Pi/Var/App fragment;
//! no arbitrary constants or axioms in binder types. Derive every constructor
//! result, motive/minor/major telescope, and applicable iota rule from source.
//! Structural comparison is sufficient here, not a completeness claim.
//! Resource caps are refusal boundaries, never shortcuts to acceptance.
use super::*;
use std::rc::Rc;

const MAX_DEPTH:usize=64;
const MAX_ARITY:usize=16;
struct Budget(usize);
impl Budget {
    fn spend(&mut self,depth:usize)->Option<()> {
        need(depth<=MAX_DEPTH && self.0>0)?;
        self.0-=1;Some(())
    }
}

type U=Rc<Universe>;
#[derive(Clone,Debug,Eq,PartialEq)]
enum Universe { Zero, Param(usize), Succ(U), Max(U,U), IMax(U,U) }
fn zero()->U {Rc::new(Universe::Zero)}
fn param(n:usize)->U {Rc::new(Universe::Param(n))}
fn succ(u:U)->U {Rc::new(Universe::Succ(u))}
fn eval_zero(u:&U,positive:bool)->bool {
    match u.as_ref() {
        Universe::Zero=>true,
        Universe::Param(_)=>!positive,
        Universe::Succ(_)=>false,
        Universe::Max(a,b)=>eval_zero(a,positive)&&eval_zero(b,positive),
        Universe::IMax(_,b)=>eval_zero(b,positive),
    }
}
fn scoped(u:&U,ps:&[usize])->bool {
    match u.as_ref(){
        Universe::Zero=>true,
        Universe::Param(n)=>ps.contains(n),
        Universe::Succ(a)=>scoped(a,ps),
        Universe::Max(a,b)|Universe::IMax(a,b)=>scoped(a,ps)&&scoped(b,ps),
    }
}
// Sound sufficient universe inequality. A zero result at every all-positive
// parameter assignment is zero everywhere (zero/nonzero is monotone).
// Never infer a comparison from a finite sample of numeric level magnitudes.
fn leq(a:&U,b:&U,fuel:&mut Budget,depth:usize)->Option<bool>{
    fuel.spend(depth)?;
    if a==b || eval_zero(a,true){return Some(true)}
    if let Universe::Succ(y)=b.as_ref(){
        if a==y || leq(a,y,fuel,depth+1)? {return Some(true)}
        if let Universe::Succ(x)=a.as_ref(){
            return leq(x,y,fuel,depth+1)
        }
    }
    if let Universe::Max(x,y)=a.as_ref(){
        return Some(leq(x,b,fuel,depth+1)?&&leq(y,b,fuel,depth+1)?)
    }
    if let Universe::Max(x,y)=b.as_ref(){
        return Some(leq(a,x,fuel,depth+1)?||leq(a,y,fuel,depth+1)?)
    }
    Some(false)
}

type T=Rc<Term>;
#[derive(Clone,Debug,Eq,PartialEq)]
enum Term { V(usize), S(U), C(usize,Vec<U>), A(T,T), P(T,T), L(T,T) }
fn var(n:usize)->T{Rc::new(Term::V(n))}
fn sort(u:U)->T{Rc::new(Term::S(u))}
fn constant(n:usize,us:&[U])->T{Rc::new(Term::C(n,us.to_vec()))}
fn app(f:T,a:T)->T{Rc::new(Term::A(f,a))}
fn pi(d:T,b:T)->T{Rc::new(Term::P(d,b))}
fn lam(d:T,b:T)->T{Rc::new(Term::L(d,b))}
fn apps(f:T,args:impl IntoIterator<Item=T>)->T{args.into_iter().fold(f,app)}
fn wrap(ds:&[T],body:T,is_lam:bool)->T{
    ds.iter().rev().fold(body,|b,d|if is_lam{lam(d.clone(),b)}else{pi(d.clone(),b)})
}
fn term_scope(t:&T,ps:&[usize])->bool{
    match t.as_ref(){
        Term::V(_)=>true,
        Term::S(u)=>scoped(u,ps),
        Term::C(_,us)=>us.iter().all(|u|scoped(u,ps)),
        Term::A(a,b)|Term::P(a,b)|Term::L(a,b)=>term_scope(a,ps)&&term_scope(b,ps),
    }
}
fn from_level(t:&Tables,id:usize,fuel:&mut Budget,depth:usize)->Option<U>{
    fuel.spend(depth)?;
    let u=match *t.levels.get(id)?{
        Level::Zero=>Universe::Zero,
        Level::Param(n)=>Universe::Param(n),
        Level::Succ(n)=>Universe::Succ(from_level(t,n,fuel,depth+1)?),
        Level::Max(a,b)=>Universe::Max(from_level(t,a,fuel,depth+1)?,from_level(t,b,fuel,depth+1)?),
        Level::IMax(a,b)=>Universe::IMax(from_level(t,a,fuel,depth+1)?,from_level(t,b,fuel,depth+1)?),
    };
    Some(Rc::new(u))
}
fn from_expr(t:&Tables,id:usize,fuel:&mut Budget,depth:usize)->Option<T>{
    fuel.spend(depth)?;
    let e=match t.exprs.get(id)?{
        Expr::BVar(n)=>Term::V(*n),
        Expr::Sort(n)=>Term::S(from_level(t,*n,fuel,depth+1)?),
        Expr::Const(n,us)=>Term::C(*n,us.iter().map(|&u|from_level(t,u,fuel,depth+1)).collect::<Option<Vec<_>>>()?),
        Expr::App(a,b)=>Term::A(from_expr(t,*a,fuel,depth+1)?,from_expr(t,*b,fuel,depth+1)?),
        Expr::Pi(a,b)=>Term::P(from_expr(t,*a,fuel,depth+1)?,from_expr(t,*b,fuel,depth+1)?),
        Expr::Lam(a,b)=>Term::L(from_expr(t,*a,fuel,depth+1)?,from_expr(t,*b,fuel,depth+1)?),
    };
    Some(Rc::new(e))
}
// Raise free de Bruijn indices only, leaving bound indices below cutoff.
fn lift(t:&T,n:usize,cutoff:usize,fuel:&mut Budget,depth:usize)->Option<T>{
    fuel.spend(depth)?;
    Some(match t.as_ref(){
        Term::V(i)=>var(if *i>=cutoff {i.checked_add(n)?}else{*i}),
        Term::S(_)|Term::C(..)=>t.clone(),
        Term::A(a,b)=>app(lift(a,n,cutoff,fuel,depth+1)?,lift(b,n,cutoff,fuel,depth+1)?),
        Term::P(a,b)=>pi(lift(a,n,cutoff,fuel,depth+1)?,lift(b,n,cutoff+1,fuel,depth+1)?),
        Term::L(a,b)=>lam(lift(a,n,cutoff,fuel,depth+1)?,lift(b,n,cutoff+1,fuel,depth+1)?),
    })
}
// Capture-avoiding substitution removing the opened binder.
fn subst(t:&T,a:&T,binder:usize,fuel:&mut Budget,depth:usize)->Option<T>{
    fuel.spend(depth)?;
    Some(match t.as_ref(){
        Term::V(i) if *i==binder=>lift(a,binder,0,fuel,depth+1)?,
        Term::V(i)=>var(if *i>binder{i-1}else{*i}),
        Term::S(_)|Term::C(..)=>t.clone(),
        Term::A(x,y)=>app(subst(x,a,binder,fuel,depth+1)?,subst(y,a,binder,fuel,depth+1)?),
        Term::P(x,y)=>pi(subst(x,a,binder,fuel,depth+1)?,subst(y,a,binder+1,fuel,depth+1)?),
        Term::L(x,y)=>lam(subst(x,a,binder,fuel,depth+1)?,subst(y,a,binder+1,fuel,depth+1)?),
    })
}
fn as_sort(t:&T)->Option<U>{if let Term::S(u)=t.as_ref(){Some(u.clone())}else{None}}
// All constructor-field and parameter-domain terms must have a type derived
// from this closed context. Arbitrary constants, lambdas, reduction and
// recursive hypotheses are not assumed available in this fragment.
fn infer(t:&T,ctx:&mut Vec<T>,fuel:&mut Budget,depth:usize)->Option<T>{
    fuel.spend(depth)?;
    match t.as_ref(){
        Term::V(i)=>{
            let k=ctx.len().checked_sub(i.checked_add(1)?)?;
            lift(ctx.get(k)?,i+1,0,fuel,depth+1)
        },
        Term::S(u)=>Some(sort(succ(u.clone()))),
        Term::P(d,b)=>{
            let x=as_sort(&infer(d,ctx,fuel,depth+1)?)?;
            ctx.push(d.clone());
            let y=as_sort(&infer(b,ctx,fuel,depth+1)?);
            ctx.pop();
            Some(sort(Rc::new(Universe::IMax(x,y?))))
        },
        Term::A(f,a)=>{
            let ft=infer(f,ctx,fuel,depth+1)?;
            let Term::P(domain,body)=ft.as_ref()else{return None};
            need(infer(a,ctx,fuel,depth+1)?==*domain)?;
            subst(body,a,0,fuel,depth+1)
        },
        _=>None,
    }
}
fn peel(mut t:T,n:usize)->Option<(Vec<T>,T)>{
    need(n<=MAX_ARITY)?;
    let mut domains=Vec::with_capacity(n);
    for _ in 0..n{
        let Term::P(d,b)=t.as_ref()else{return None};
        domains.push(d.clone());t=b.clone();
    }
    Some((domains,t))
}
fn family(i:usize,us:&[U],params:usize,depth:usize)->Option<T>{
    need(depth>=params)?;
    Some(apps(constant(i,us),(0..params).map(|j|var(depth-1-j))))
}
fn fresh_motive(t:&Tables,ps:&[usize],name:usize)->bool{
    for j in 0..=ps.len(){
        let s=if j==0{"u".to_owned()}else{format!("u_{j}")};
        if !ps.iter().any(|&n|t.name(n,0,&s)){
            return t.name(name,0,&s)
        }
    }
    false
}

pub(super) fn block(t:&Tables,b:&Value)->Option<()>{
    let mut fuel=Budget(100_000);
    need(keys(b,&["types","ctors","recs"]))?;
    let types=arr(b,"types")?;let constructors=arr(b,"ctors")?;let recs=arr(b,"recs")?;
    need(types.len()==1&&recs.len()==1&&constructors.len()<=MAX_ARITY)?;
    let ind=&types[0];let rec=&recs[0];
    need(keys(ind,&["all","ctors","hasEta","hasLargeElim","hasProjections","isImpredicative",
        "isK","isRec","isUnsafe","levelParams","name","numIndices","numNested","numParams","type"]))?;
    need(keys(rec,&["all","isUnsafe","k","levelParams","name","numIndices","numMinors",
        "numMotives","numParams","rules","type"]))?;
    let i=num(ind,"name")?;let r=num(rec,"name")?;let p=num(ind,"numParams")?;
    let ctors=numbers(ind,"ctors")?;let n=ctors.len();
    let ps=numbers(ind,"levelParams")?;
    need(p<=MAX_ARITY&&ps.len()<=MAX_ARITY&&n==constructors.len())?;
    need(t.valid_name(i)&&t.valid_name(r)&&t.name(r,i,"rec"))?;
    let mut declared=HashSet::from([i,r]);
    need(declared.len()==2&&ctors.iter().all(|&x|t.valid_name(x)&&declared.insert(x)))?;
    let mut seen=HashSet::new();
    need(ps.iter().all(|&x|t.valid_name(x)&&seen.insert(x)))?;
    need(numbers(ind,"all")?==[i]&&num(ind,"numIndices")?==0&&num(ind,"numNested")?==0&&
        !boolean(ind,"isRec")?&&!boolean(ind,"isUnsafe")?)?;
    let us=ps.iter().map(|&u|param(u)).collect::<Vec<_>>();
    let ind_type=from_expr(t,num(ind,"type")?,&mut fuel,0)?;
    need(term_scope(&ind_type,&ps))?;
    let (params,tail)=peel(ind_type,p)?;
    let level=as_sort(&tail)?;
    let mut ctx=Vec::new();
    for d in &params{
        as_sort(&infer(d,&mut ctx,&mut fuel,0)?)?;
        ctx.push(d.clone());
    }
    let f=Features::read(ind).ok()?;
    need(!f.imp||eval_zero(&level,true))?;
    need(!f.projections||(n==1&&!f.imp))?;
    need(!f.eta||f.projections)?;
    need(!f.k||(n==1&&eval_zero(&level,true)&&num(&constructors[0],"numFields")?==0))?;
    need(!f.large||(!f.imp&&(!eval_zero(&level,false)||n==0||(n==1&&(f.eta||f.k)))))?;
    let mut fields=Vec::<Vec<T>>::new();
    for (j,c) in constructors.iter().enumerate(){
        need(keys(c,&["cidx","induct","isUnsafe","levelParams","name","numFields","numParams","type"]))?;
        need(num(c,"name")?==ctors[j]&&num(c,"induct")?==i&&num(c,"cidx")?==j&&
            num(c,"numParams")?==p&&!boolean(c,"isUnsafe")?&&numbers(c,"levelParams")?==ps)?;
        let ctype=from_expr(t,num(c,"type")?,&mut fuel,0)?;
        need(term_scope(&ctype,&ps))?;
        let (cparams,body)=peel(ctype,p)?;need(cparams==params)?;
        let (fs,end)=peel(body,num(c,"numFields")?)?;
        need(end==family(i,&us,p,p+fs.len())?)?;
        let mut cx=params.clone();
        for d in &fs{
            let u=as_sort(&infer(d,&mut cx,&mut fuel,0)?)?;
            need(f.imp||leq(&u,&level,&mut fuel,0)?)?;
            cx.push(d.clone());
        }
        fields.push(fs);
    }
    need(numbers(rec,"all")?==[i]&&!boolean(rec,"isUnsafe")?&&boolean(rec,"k")?==f.k&&
        num(rec,"numIndices")?==0&&num(rec,"numParams")?==p&&num(rec,"numMinors")?==n&&num(rec,"numMotives")?==1)?;
    let rps=numbers(rec,"levelParams")?;
    let motive=if f.large{
        need(rps.len()==ps.len()+1&&rps[1..]==ps&&t.valid_name(rps[0])&&fresh_motive(t,&ps,rps[0]))?;
        param(rps[0])
    }else{need(rps==ps)?;zero()};
    let mut common=params.clone();
    common.push(pi(family(i,&us,p,p)?,sort(motive)));
    for (j,fs) in fields.iter().enumerate(){
        let q=fs.len();let depth=p+1+j+q;
        let args=(0..p).map(|k|var(depth-1-k)).chain((0..q).map(|k|var(q-1-k)));
        let c=apps(constant(ctors[j],&us),args);
        let ds=fs.iter().enumerate().map(|(k,d)|lift(d,1+j,k,&mut fuel,0)).collect::<Option<Vec<_>>>()?;
        common.push(wrap(&ds,app(var(j+q),c),false));
    }
    let mut rec_binders=common.clone();
    rec_binders.push(family(i,&us,p,p+1+n)?);
    let expected=wrap(&rec_binders,app(var(n+1),var(0)),false);
    let actual=from_expr(t,num(rec,"type")?,&mut fuel,0)?;
    need(actual==expected)?;
    let rules=arr(rec,"rules")?;
    need(rules.len()==if f.large{n}else{0})?;
    for (j,rule) in rules.iter().enumerate(){
        let fs=&fields[j];let q=fs.len();
        need(keys(rule,&["ctor","nfields","rhs"])&&num(rule,"ctor")?==ctors[j]&&num(rule,"nfields")?==q)?;
        let mut binders=common.clone();
        for (k,d) in fs.iter().enumerate(){binders.push(lift(d,1+n,k,&mut fuel,0)?)}
        let rhs=wrap(&binders,apps(var(n-1-j+q),(0..q).map(|k|var(q-1-k))),true);
        need(from_expr(t,num(rule,"rhs")?,&mut fuel,0)?==rhs)?;
    }
    Some(())
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]
    fn substitution_and_lifting_are_capture_avoiding(){
        let mut fuel=Budget(1000);
        let t=pi(var(0),app(var(1),var(0)));
        assert_eq!(lift(&t,2,0,&mut fuel,0),Some(pi(var(2),app(var(3),var(0)))));
        assert_eq!(subst(&t,&var(0),0,&mut fuel,0),Some(pi(var(0),app(var(1),var(0)))));
    }
    #[test]
    fn dependent_field_and_universe_constraints(){
        let mut fuel=Budget(1000);
        let u=param(1);
        // α : Sort u, p : α -> Prop, w : α
        let mut cx=vec![sort(u.clone()),pi(var(0),sort(zero())),var(1)];
        let field=app(var(1),var(0));
        assert_eq!(infer(&field,&mut cx,&mut fuel,0),Some(sort(zero())));
        assert_eq!(leq(&u,&zero(),&mut fuel,0),Some(false));
        assert_eq!(leq(&zero(),&u,&mut fuel,0),Some(true));
        assert_eq!(leq(&u,&u,&mut fuel,0),Some(true));
        assert_eq!(infer(&var(9),&mut cx,&mut fuel,0),None);
    }
}
