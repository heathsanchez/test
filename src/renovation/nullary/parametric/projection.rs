//! Bounded compositional admission: one independently reconstructed family,
//! followed by one safe declaration. No imported constants, reduction,
//! proof irrelevance, or eta are assumed. Unsupported conversion is UNKNOWN.
use super::*;
use super::super::super::Outcome;

#[derive(Debug,PartialEq,Eq)]
enum Failure { Unknown, ForbiddenProjection, OutOfRange }
type R<T> = Result<T,Failure>;
fn known<T>(x:Option<T>)->R<T>{x.ok_or(Failure::Unknown)}
fn require(ok:bool)->R<()>{known(need(ok))}
fn projection(n:usize,i:usize,s:T)->T{Rc::new(Term::Proj(n,i,s))}

// Simultaneous capture-avoiding instantiation of the source field
// telescope. Arguments are in outermost-first order in the caller context.
fn instantiate(t:&T,args:&[T],cutoff:usize,fuel:&mut Budget,depth:usize)->Option<T>{
    fuel.spend(depth)?;
    Some(match t.as_ref(){
        Term::V(i) if *i<cutoff=>t.clone(),
        Term::V(i)=>lift(args.get(args.len().checked_sub(i-cutoff+1)?)?,cutoff,0,fuel,depth+1)?,
        Term::S(_)|Term::C(..)=>t.clone(),
        Term::A(a,b)=>app(instantiate(a,args,cutoff,fuel,depth+1)?,instantiate(b,args,cutoff,fuel,depth+1)?),
        Term::P(a,b)=>pi(instantiate(a,args,cutoff,fuel,depth+1)?,instantiate(b,args,cutoff+1,fuel,depth+1)?),
        Term::L(a,b)=>lam(instantiate(a,args,cutoff,fuel,depth+1)?,instantiate(b,args,cutoff+1,fuel,depth+1)?),
        Term::Proj(i,j,s)=>projection(*i,*j,instantiate(s,args,cutoff,fuel,depth+1)?),
    })
}
fn family_args(ty:&T,f:&Family)->Option<Vec<T>>{
    let mut head=ty;let mut args=Vec::new();
    while let Term::A(a,b)=head.as_ref(){
        if args.len()>=MAX_ARITY{return None}
        args.push(b.clone());head=a;
    }
    need(matches!(head.as_ref(),Term::C(n,us) if *n==f.name&&us.is_empty())&&args.len()==f.params)?;
    args.reverse();Some(args)
}
fn infer_checked(t:&T,cx:&mut Vec<T>,f:&Family,fuel:&mut Budget,depth:usize,used:&mut bool)->R<T>{
    known(fuel.spend(depth))?;
    match t.as_ref(){
        Term::V(i)=>{
            let n=known(i.checked_add(1))?;
            let k=known(cx.len().checked_sub(n))?;
            known(lift(known(cx.get(k))?,n,0,fuel,depth+1))
        },
        Term::S(u)=>Ok(sort(succ(u.clone()))),
        Term::C(n,us)=>{
            require(*n==f.name&&us.is_empty())?;
            Ok(f.ty.clone())
        },
        Term::P(d,b)|Term::L(d,b)=>{
            let domain_sort=known(as_sort(&infer_checked(d,cx,f,fuel,depth+1,used)?))?;
            cx.push(d.clone());
            let body=infer_checked(b,cx,f,fuel,depth+1,used);
            cx.pop();
            let body=body?;
            if matches!(t.as_ref(),Term::L(..)){Ok(pi(d.clone(),body))}
            else{Ok(sort(Rc::new(Universe::IMax(domain_sort,known(as_sort(&body))?))))}
        },
        Term::A(a,b)=>{
            let ty=infer_checked(a,cx,f,fuel,depth+1,used)?;
            let Term::P(domain,body)=ty.as_ref()else{return Err(Failure::Unknown)};
            require(infer_checked(b,cx,f,fuel,depth+1,used)?==*domain)?;
            known(subst(body,b,0,fuel,depth+1))
        },
        Term::Proj(n,i,s)=>{
            require(*n==f.name)?;
            // Derive the scrutinee's actual type before any refutation.
            let st=infer_checked(s,cx,f,fuel,depth+1,used)?;
            let mut args=known(family_args(&st,f))?;
            if !f.projections{return Err(Failure::ForbiddenProjection)}
            require(f.fields.len()==1)?;
            let fields=&f.fields[0];
            let field=fields.get(*i).ok_or(Failure::OutOfRange)?;
            for j in 0..*i {args.push(projection(*n,j,s.clone()));}
            let ty=known(instantiate(field,&args,0,fuel,depth+1))?;
            *used=true;
            Ok(ty)
        }
    }
}
fn decl(t:&Tables,row:&Value,f:&Family)->R<()>{
    // Initial experiment deliberately limits the family and declaration
    // to zero universe parameters; no conversion, recursive or mutual defs.
    require(f.universes.is_empty())?;
    let d=if keys(row,&["def"]){
        let d=known(row.get("def"))?;
        require(keys(d,&["name","levelParams","type","value","hints","safety","all"]))?;
        require(d.get("safety").and_then(Value::as_str)==Some("safe"))?;
        let h=known(d.get("hints"))?;
        require(matches!(h.as_str(),Some("opaque"|"abbrev"))||(keys(h,&["regular"])&&num(h,"regular").is_some()))?;
        d
    }else if keys(row,&["thm"]){
        let d=known(row.get("thm"))?;
        require(keys(d,&["name","levelParams","type","value","all"]))?;
        d
    }else{return Err(Failure::Unknown)};
    let name=known(num(d,"name"))?;
    require(t.valid_name(name)&&!f.declared.contains(&name)&&known(numbers(d,"all"))?==[name]&&known(numbers(d,"levelParams"))?.is_empty())?;
    let mut fuel=Budget(100_000);
    let ty=known(from_expr(t,known(num(d,"type"))?,&mut fuel,0))?;
    let val=known(from_expr(t,known(num(d,"value"))?,&mut fuel,0))?;
    require(term_scope(&ty,&[])&&term_scope(&val,&[]))?;
    let mut used=false;
    let mut cx=Vec::new();
    known(as_sort(&infer_checked(&ty,&mut cx,f,&mut fuel,0,&mut used)?))?;
    require(infer_checked(&val,&mut cx,f,&mut fuel,0,&mut used)?==ty)?;
    require(used)
}
pub(in crate::renovation) fn projection_export(rows:&[Value])->Option<Outcome>{
    let (last,prefix)=rows.split_last()?;
    let mut t=Tables::new();
    let mut f=None;
    for row in prefix{
        if keys(row,&["inductive"]){
            need(f.is_none())?;
            f=Some(checked_family(&t,row.get("inductive")?)?);
        }else if row.get("proj").is_some(){
            need(f.is_some())?;
            t.add_projection(row)?;
        }else{t.add(row)?;}
    }
    match decl(&t,last,&f?){
        Ok(())=>Some(Outcome::AcceptReconstructed),
        Err(Failure::ForbiddenProjection)=>Some(Outcome::Reject("checked-family-projection-forbidden")),
        Err(Failure::OutOfRange)=>Some(Outcome::Reject("checked-family-projection-index")),
        Err(Failure::Unknown)=>None,
    }
}
#[cfg(test)]
mod tests{
    use super::*;
    #[test]
    fn dependent_field_instantiation_preserves_binder_scope(){
        let mut fuel=Budget(1000);
        // Field type p x under telescope [p,x]; a binder inside its type
        // must not capture the caller's variables.
        let src=pi(var(0),app(var(2),var(1)));
        let args=[var(4),var(2)];
        assert_eq!(instantiate(&src,&args,0,&mut fuel,0),Some(pi(var(2),app(var(5),var(3)))));
    }
    #[test]
    fn projection_type_uses_prior_field_of_same_scrutinee(){
        let mut fuel=Budget(1000);
        let s=var(0);
        let args=[var(1),projection(7,0,s.clone())];
        let src=app(var(1),var(0));
        assert_eq!(instantiate(&src,&args,0,&mut fuel,0),Some(app(var(1),projection(7,0,s))));
    }
}
