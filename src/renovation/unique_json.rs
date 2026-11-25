//! Decode object keys before comparing them, at every nesting level.
//! Key order is not part of the JSON meaning. A duplicate key (including
//! an escaped spelling of the same decoded key) is never silently erased.
use serde::de::{self, Deserialize, Deserializer, MapAccess, SeqAccess, Visitor};
use serde_json::{Map, Number, Value};
use std::fmt;

struct Unique(Value);
struct UniqueVisitor;

impl<'de> Deserialize<'de> for Unique {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        d.deserialize_any(UniqueVisitor)
    }
}
impl<'de> Visitor<'de> for UniqueVisitor {
    type Value = Unique;
    fn expecting(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
        f.write_str("JSON with unique decoded object keys")
    }
    fn visit_bool<E:de::Error>(self,v:bool)->Result<Unique,E>{Ok(Unique(Value::Bool(v)))}
    fn visit_i64<E:de::Error>(self,v:i64)->Result<Unique,E>{Ok(Unique(Value::Number(v.into())))}
    fn visit_u64<E:de::Error>(self,v:u64)->Result<Unique,E>{Ok(Unique(Value::Number(v.into())))}
    fn visit_f64<E:de::Error>(self,v:f64)->Result<Unique,E>{
        Number::from_f64(v).map(|n|Unique(Value::Number(n))).ok_or_else(||E::custom("nonfinite JSON number"))
    }
    fn visit_str<E:de::Error>(self,v:&str)->Result<Unique,E>{Ok(Unique(Value::String(v.to_owned())))}
    fn visit_string<E:de::Error>(self,v:String)->Result<Unique,E>{Ok(Unique(Value::String(v)))}
    fn visit_unit<E:de::Error>(self)->Result<Unique,E>{Ok(Unique(Value::Null))}
    fn visit_none<E:de::Error>(self)->Result<Unique,E>{Ok(Unique(Value::Null))}
    fn visit_seq<A:SeqAccess<'de>>(self,mut a:A)->Result<Unique,A::Error>{
        let mut items=Vec::new();
        while let Some(Unique(v))=a.next_element::<Unique>()?{items.push(v)}
        Ok(Unique(Value::Array(items)))
    }
    fn visit_map<A:MapAccess<'de>>(self,mut a:A)->Result<Unique,A::Error>{
        let mut obj=Map::new();
        while let Some(k)=a.next_key::<String>()?{
            if obj.contains_key(&k){return Err(de::Error::custom("duplicate decoded object key"))}
            let Unique(v)=a.next_value::<Unique>()?;
            obj.insert(k,v);
        }
        Ok(Unique(Value::Object(obj)))
    }
}
pub(super) fn parse(s:&str)->Result<Value,serde_json::Error>{
    serde_json::from_str::<Unique>(s).map(|Unique(v)|v)
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]
    fn order_and_whitespace_are_semantically_inert(){
        assert_eq!(parse(r#"{"z": 1, "a": {"y": true,"x": []}}"#).unwrap(),
                   parse(r#"{"a":{"x":[],"y":true},"z":1}"#).unwrap());
    }
    #[test]
    fn duplicates_rejected_including_decoded_aliases(){
        for s in [r#"{"x":1,"x":1}"#,r#"{"outer":[{"x":1,"x":2}]}"#,
                  r#"{"x":1,"\u0078":2}"#]{
            assert!(parse(s).is_err());
        }
    }
}
