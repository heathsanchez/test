// Conservative allocation-free recognizer for common numeric records.
// Anything outside this exact JSON subset uses the original parser.
enum HotRecord { Expr(u64,Expr), Level(u64,Level) }
struct HotCursor<'a> { b:&'a [u8], i:usize }
impl<'a> HotCursor<'a> {
 fn ws(&mut self){while self.i<self.b.len() && matches!(self.b[self.i],b' '|b'\t'|b'\r'|b'\n'){self.i+=1;}}
 fn eat(&mut self,c:u8)->Option<()> {self.ws();if self.b.get(self.i).copied()!=Some(c){return None;}self.i+=1;Some(())}
 fn key(&mut self)->Option<&'a [u8]>{self.eat(b'"')?;let start=self.i;while let Some(&c)=self.b.get(self.i){if c==b'"'{let key=&self.b[start..self.i];self.i+=1;self.eat(b':')?;return Some(key);}if c==b'\\'||c<32{return None;}self.i+=1;}None}
 fn num(&mut self)->Option<u64>{self.ws();let start=self.i;let mut n=0u64;while let Some(&c)=self.b.get(self.i){if !c.is_ascii_digit(){break;}n=n.checked_mul(10)?.checked_add((c-b'0') as u64)?;self.i+=1;}if self.i==start || (self.i>start+1&&self.b[start]==b'0'){return None;}Some(n)}
 fn fields<const N:usize>(&mut self,keys:[&[u8];N])->Option<[u64;N]>{self.eat(b'{')?;let mut a=[0u64;N];let mut seen=[false;N];for j in 0..N {if j>0{self.eat(b',')?;}let k=self.key()?;let i=keys.iter().position(|x|*x==k)?;if seen[i]{return None;}seen[i]=true;a[i]=self.num()?;}self.eat(b'}')?;if seen.iter().all(|x|*x){Some(a)}else{None}}
 fn pair(&mut self)->Option<(u64,u64)>{self.eat(b'[')?;let a=self.num()?;self.eat(b',')?;let b=self.num()?;self.eat(b']')?;Some((a,b))}
}
fn hot_record(line:&str)->Option<HotRecord>{
 let mut c=HotCursor{b:line.as_bytes(),i:0};c.eat(b'{')?;
 // Canonical ID-first order only. Reordered keys use the general parser.
 let table=c.key()?;if table!=b"ie"&&table!=b"il"{return None;}
 let id=c.num()?;c.eat(b',')?;let tag=c.key()?;
 let record=if table==b"ie" {HotRecord::Expr(id,match tag {
  b"bvar"=>Expr::BVar(c.num()?),b"sort"=>Expr::Sort(LevelId(c.num()?)),
  b"app"=>{let [f,a]=c.fields([b"fn".as_slice(),b"arg".as_slice()])?;Expr::App{fun:ExprId(f),arg:ExprId(a)}},
  b"lam"|b"forallE"=>{let [d,b]=c.fields([b"type".as_slice(),b"body".as_slice()])?;if tag==b"lam"{Expr::Lam{domain:ExprId(d),body:ExprId(b)}}else{Expr::Pi{domain:ExprId(d),body:ExprId(b)}}},
  b"letE"=>{let [t,v,b]=c.fields([b"type".as_slice(),b"value".as_slice(),b"body".as_slice()])?;Expr::Let{ty:ExprId(t),value:ExprId(v),body:ExprId(b)}},
  b"proj"=>{let [t,i,s]=c.fields([b"typeName".as_slice(),b"idx".as_slice(),b"struct".as_slice()])?;Expr::Proj{type_name:NameId(t),index:i,structure:ExprId(s)}},
  _=>return None,
 })}else{HotRecord::Level(id,match tag{
  b"succ"=>Level::Succ(LevelId(c.num()?)),b"param"=>Level::Param(NameId(c.num()?)),
  b"max"|b"imax"=>{let(a,b)=c.pair()?;if tag==b"max"{Level::Max(LevelId(a),LevelId(b))}else{Level::IMax(LevelId(a),LevelId(b))}},_=>return None,
 })};
 c.eat(b'}')?;c.ws();if c.i!=c.b.len(){return None;}Some(record)
}
fn apply_hot(export:&mut ParsedExport,r:HotRecord)->Result<(),ParseError>{match r{HotRecord::Expr(i,e)=>export.exprs.insert(ExprId(i),e)?,HotRecord::Level(i,l)=>export.levels.insert(LevelId(i),l)?};Ok(())}

fn strip_line_ending(line:&mut String){if line.ends_with('\n'){line.pop();if line.ends_with('\r'){line.pop();}}}

pub fn parse<R:BufRead>(mut reader:R)->Result<ParsedExport,ParseError>{
 let mut line=String::new();
 if reader.read_line(&mut line).map_err(|e|ParseError::Io{line:1,message:e.to_string()})?==0{return Err(ParseError::MissingMeta);}
 strip_line_ending(&mut line);
 let meta=parse_meta(parse_json(&line,1)?)?;
 let mut export=ParsedExport{meta,names:IdTable::default(),levels:IdTable::default(),exprs:IdTable::default(),declarations:Vec::new()};
 export.levels.insert(LevelId(0),Level::Zero)?;
 let mut line_number=1;let mut hot_hits=0u64;let mut records=0u64;
 loop{line.clear();line_number+=1;let n=reader.read_line(&mut line).map_err(|e|ParseError::Io{line:line_number,message:e.to_string()})?;if n==0{break;}strip_line_ending(&mut line);records+=1;
  if let Some(record)=hot_record(&line){hot_hits+=1;apply_hot(&mut export,record)?;}else{parse_record(&mut export,parse_json(&line,line_number)?,line_number)?;}
 }
 if std::env::var_os("NUCLEUS_TRACE_IMPORT").is_some(){eprintln!("IMPORT_RECORDS {records} HOT_RECORDS {hot_hits}");}
 Ok(export)
}

#[cfg(test)]
mod hot_differential_tests {
 use super::*;
 fn blank()->ParsedExport {parse_reference(std::io::Cursor::new("{\"meta\":{\"format\":{\"version\":\"3.1.0\"}}}\n")).unwrap()}
 fn same(a:&ParsedExport,b:&ParsedExport){assert_eq!(a.meta.raw,b.meta.raw);assert_eq!(a.names.len(),b.names.len());for(i,v)in a.names.iter_raw(){assert_eq!(Some(v),b.names.get(NameId(i)));}assert_eq!(a.levels.len(),b.levels.len());for(i,v)in a.levels.iter_raw(){assert_eq!(Some(v),b.levels.get(LevelId(i)));}assert_eq!(a.exprs.len(),b.exprs.len());for(i,v)in a.exprs.iter_raw(){assert_eq!(Some(v),b.exprs.get(ExprId(i)));}assert_eq!(a.declarations,b.declarations);}
 fn compare(s:&str){let input=format!("{{\"meta\":{{\"format\":{{\"version\":\"3.1.0\"}}}}}}\n{s}");let a=parse(std::io::Cursor::new(&input));let b=parse_reference(std::io::Cursor::new(&input));match(a,b){(Ok(a),Ok(b))=>same(&a,&b),(Err(a),Err(b))=>assert_eq!(a,b,"{s}"),_=>panic!("parser disagreement: {s}")}}
 #[test]fn valid_and_hostile_numeric_records_match_reference(){
  for n in 0..2000u64 {for s in [format!("{{\"ie\":{n},\"app\":{{\"fn\":{},\"arg\":{}}}}}",n+1,n+2),format!("{{\"ie\":{n},\"bvar\":{n}}}"),format!("{{\"ie\":{n},\"sort\":{n}}}"),format!("{{\"il\":{},\"max\":[{n},{}]}}",n+1,n+2),format!("{{\"ie\":{n},\"letE\":{{\"body\":1,\"type\":2,\"value\":3}}}}")]{assert!(hot_record(&s).is_some());compare(&s);compare(&s.replace(":",": ").replace(",",",\t"));compare(&(s.clone()+" garbage"));compare(&s.replacen(&format!(":{n}"),":18446744073709551616",1));}}
  for s in [r#"{"ie":0,"bvar":01}"#,r#"{"ie":0,"bvar":1e2}"#,r#"{"ie":0,"bvar":1.0}"#,r#"{"ie":0,"bvar":-0}"#,r#"{"ie":0,"bvar":true}"#,r#"{"ie":0,"app":{"fn":1,"fn":2,"arg":3}}"#,r#"{"ie":0,"bvar":1,"sort":0}"#,r#"{"ie":1,"ie":2,"bvar":1}"#,r#"{"ie":0,"app":{"fn":1,"arg":2,"extra":3}}"#,r#"{"bvar":1,"ie":0}"#,r#"{"ie":0,"b\u0076ar":1}"#,r#"{"il":0,"succ":0}"#,r#"{"ie":0,"proj":{"idx":1,"struct":2,"typeName":3}}"#,r#"{"ie":0,"lam":{"type":1,"body":2}}"#,r#"{"ie":0,"forallE":{"body":2,"type":1}}"#,r#"{"il":1,"imax":[0,1]}"#,r#"{"il":1,"param":0}"#]{compare(s);}
  compare("{\"ie\":0,\"bvar\":0}\n{\"ie\":0,\"bvar\":1}");compare("{\"ie\":0,\"bvar\":0}\r\n");compare("\n");
 }
 #[test]fn every_recognized_byte_mutation_is_valid_reference_json(){
  let seed=br#"{"ie":17,"app":{"fn":23,"arg":29}}"#;
  for i in 0..seed.len(){for c in 0u8..128{let mut b=seed.to_vec();b[i]=c;let s=std::str::from_utf8(&b).unwrap();if let Some(h)=hot_record(s){let mut a=blank();let mut b=blank();apply_hot(&mut a,h).unwrap();let v=parse_json(s,2).unwrap();parse_record(&mut b,v,2).unwrap();same(&a,&b);}}}
 }
}
