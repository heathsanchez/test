#[cfg(test)]
mod qualified_nullary_enum_reductions {
    use super::*;
    use crate::machine::Machine;
    use crate::value::Closure;
    #[test]
    fn all_three_source_constructor_branches_reduce_to_their_distinct_numerals() {
        let source=include_str!("../tests/fixtures/nullary-enum/enum3.ndjson");
        assert_eq!(crate::run(std::io::Cursor::new(source)),Verdict::Accept);
        let export=crate::parser::parse(std::io::Cursor::new(source)).unwrap().resolve().unwrap();
        let mut environment=Environment::empty();
        for declaration in &export.declarations {
            if let Declaration::Inductive(block)=declaration {
                environment=check_inductive(&export,&environment,block,Limits::default(),DeltaPolicy::GuardedSemanticFallback).unwrap();
            }
        }
        let machine=Machine::new(environment.authority(),&export.exprs,&export.levels,environment.definition_bodies())
            .with_recursor_reductions(environment.recursor_reductions())
            .with_nat_primitives(environment.nat_primitives().cloned());
        let values=export.declarations.iter().filter_map(|d|if let Declaration::Definition{value,..}=d{Some(*value)}else{None}).collect::<Vec<_>>();
        assert_eq!(values.len(),3);
        for (value,expected) in values.iter().zip(["11","23","47"]) {
            let result=machine.expose(Closure::new(*value,EnvFrame::empty()),Transparency::Full,4096);
            assert_eq!(result.proven_value(),Some(&Value::NatLit(crate::nat::BigNat::parse_decimal(expected).unwrap())));
        }
    }
}
