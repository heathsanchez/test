use metatron_kernel::verdict::Verdict;
fn run(bytes:&'static [u8])->Verdict{
 std::thread::Builder::new().stack_size(64*1024*1024)
  .spawn(move||metatron_kernel::run(std::io::Cursor::new(bytes))).unwrap().join().unwrap()
}
#[test]fn dependent_final_proof_argument_converts_under_checked_data_prefix(){
 assert_eq!(run(include_bytes!("fixtures/final-proof/dependent_proof_last.ndjson")),Verdict::Accept);
}
#[test]fn source_rec_on_swap_export_accepts(){
 assert_eq!(run(include_bytes!("fixtures/final-proof/recOnSwap-prefix.ndjson")),Verdict::Accept);
}
#[test]fn proof_congruence_does_not_erase_data_or_change_predicate_heads(){
 for(name,bytes)in [
  ("different preceding data",include_bytes!("fixtures/final-proof/wrong_data.ndjson").as_slice()),
  ("different predicate",include_bytes!("fixtures/final-proof/wrong_head.ndjson").as_slice()),
  ("final data is not proof",include_bytes!("fixtures/final-proof/data_slot.ndjson").as_slice()),
  ("different proposition",include_bytes!("fixtures/final-proof/wrong_prop.ndjson").as_slice()),
 ]{assert_ne!(run(bytes),Verdict::Accept,"{name}");}
}

#[test]fn all_five_data_prefix_positions_remain_obligations(){
 assert_eq!(run(include_bytes!("fixtures/final-proof/long_prefix_valid.ndjson")),Verdict::Accept);
 for bytes in [include_bytes!("fixtures/final-proof/long_prefix_wrong_0.ndjson").as_slice(),include_bytes!("fixtures/final-proof/long_prefix_wrong_1.ndjson").as_slice(),include_bytes!("fixtures/final-proof/long_prefix_wrong_2.ndjson").as_slice(),include_bytes!("fixtures/final-proof/long_prefix_wrong_3.ndjson").as_slice(),include_bytes!("fixtures/final-proof/long_prefix_wrong_4.ndjson").as_slice()]{assert_ne!(run(bytes),Verdict::Accept);}
}
