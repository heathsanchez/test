use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, NameId};

#[test]
fn theorem_signature_has_no_delta_body() {
    let environment = Environment::empty()
        .extend(NameId(7), ConstantDecl::theorem(vec![], ExprId(11)))
        .unwrap();

    let declaration = environment.get(NameId(7)).unwrap();
    assert_eq!(declaration.ty, ExprId(11));
    assert!(declaration.value.is_none());
    assert!(!environment.definition_bodies().contains_key(&NameId(7)));
}
