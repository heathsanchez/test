use metatron_kernel::id::{ExprId, IdTable, LevelId};

#[test]
fn sparse_and_out_of_order_ids_are_independent() {
    let mut table = IdTable::<LevelId, &'static str>::default();
    table.insert(LevelId(2), "child").unwrap();
    table.insert(LevelId(1), "parent").unwrap();

    assert_eq!(table.get(LevelId(2)), Some(&"child"));
    assert_eq!(table.get(LevelId(1)), Some(&"parent"));
    assert!(table.contains(LevelId(2)));
    assert_eq!(table.len(), 2);
}

#[test]
fn duplicate_id_is_rejected_with_table_kind_and_numeric_id() {
    let mut table = IdTable::<ExprId, u8>::default();
    table.insert(ExprId(4), 1).unwrap();

    let error = table.insert(ExprId(4), 2).unwrap_err();
    assert_eq!(error.kind(), "expression");
    assert_eq!(error.id(), 4);
    assert_eq!(table.get(ExprId(4)), Some(&1));
}
