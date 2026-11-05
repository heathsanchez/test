from pathlib import Path
import shutil
r=Path(__file__).resolve().parent;s=r/'source';shutil.copytree('/tmp/nucleus-metered-projection-chain/source',s)
p=s/'src/convert.rs';text=p.read_text();start=text.index('fn metered_projection_chain(');end=text.index('\n#[cfg(test)]\nmod metered_projection_chain_controls',start);body=text[start:end];at=body.index('    enum Task');head,tail=body[:at],body[at:];tail=tail.replace('return false','return declined!()');macro='''    macro_rules! declined{()=>{{chain_leaf_observer::record(checker,format!("decline line={} root=({},{}) remaining={}",line!(),left.expr.0,right.expr.0,*work));false}};}
''';tail=tail.replace('let k=key(&a,&b);owners.0.push', 'let k=key(&a,&b);chain_leaf_observer::record(checker,format!("enter root=({},{}) leaf={k:?} depth={depth} context={} remaining={}",left.expr.0,right.expr.0,context.len(),*work));owners.0.push')
tail=tail.replace('let(Judgment::Proven{value:a,..}', 'chain_leaf_observer::record(checker,format!("exposure root=({},{}) left={} right={} remaining={}",left.expr.0,right.expr.0,chain_leaf_observer::kind(&a),chain_leaf_observer::kind(&b),*work));let(Judgment::Proven{value:a,..}')
text=text[:start]+head+macro+tail+text[end:]
text+='''
pub(crate)mod chain_leaf_observer{
 use super::*;use std::cell::{Cell,RefCell};use std::collections::VecDeque;
 thread_local!{static TARGET:Cell<usize>=const{Cell::new(0)};static ROWS:RefCell<VecDeque<String>>=RefCell::new(VecDeque::new());}
 pub(crate)struct Scope(bool);impl Scope{pub(crate)fn new(checker:&TypeChecker<'_>,active:bool)->Self{if active{TARGET.set(checker as *const _ as usize);ROWS.with(|r|r.borrow_mut().clear());}Self(active)}}
 impl Drop for Scope{fn drop(&mut self){if self.0{TARGET.set(0);ROWS.with(|r|for row in r.borrow().iter(){eprintln!("CHAIN_LEAF_OBSERVER:{row}");});}}}
 pub(crate)fn record(checker:&TypeChecker<'_>,row:String){if TARGET.get()!=checker as *const _ as usize{return}ROWS.with(|r|{let mut r=r.borrow_mut();if r.len()==128{r.pop_front();}r.push_back(row);});}
 pub(crate)fn kind(j:&Judgment<Value>)->String{match j{Judgment::Proven{value,..}=>match value{Value::Sort(_)=>"Sort",Value::Pi{..}=>"Pi",Value::Lam{..}=>"Lam",Value::NatLit(_)=>"Nat",Value::Neutral(_)=>"Neutral",Value::StuckProjection{..}=>"StuckProjection"}.into(),Judgment::Unknown{residual}=>format!("UNKNOWN:{residual:?}"),Judgment::Refuted{obstruction}=>format!("REFUTED:{obstruction:?}")}}
}
''';p.write_text(text)
p=s/'src/checker.rs';text=p.read_text();old='''                .with_delta_policy(delta_policy);
                if let Err(verdict) = trace_verdict_boundary(
                    &export,
                    name,
                    "theorem.proposition",''';new='''                .with_delta_policy(delta_policy);
                let _leaf_observation=crate::convert::chain_leaf_observer::Scope::new(&checker,name==NameId(26127));
                if let Err(verdict) = trace_verdict_boundary(
                    &export,
                    name,
                    "theorem.proposition",''';assert text.count(old)==1;text=text.replace(old,new);p.write_text(text)
run=Path('/tmp/nucleus-conversion-reuse-observer/run.py').read_text();(r/'run.py').write_text(run)
