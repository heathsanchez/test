use metatron_kernel::mgso::SemanticObject;

fn sample() -> SemanticObject {
    SemanticObject {
        type_id: "unknown.example".to_owned(),
        contract_version: 1,
        interfaces: vec!["z".to_owned(), "a".to_owned(), "a".to_owned()],
        payload: vec![0xde, 0xad],
    }
}

fn golden() -> Vec<u8> {
    const HEX: &str = concat!(
        "4d47534f00010000000f756e6b6e6f776e2e6578616d706c65",
        "00000001000000020000000161000000017a0000000000000002dead"
    );
    (0..HEX.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&HEX[i..i + 2], 16).unwrap())
        .collect()
}

#[test]
fn mgso_golden_bytes_match_the_original_python_envelope_contract() {
    let bytes = sample().encode().unwrap();
    assert_eq!(bytes, golden());
    assert_eq!(
        sample().id().unwrap(),
        "semantic:b4673e6cc939f6c14c8c410031c898df9ff24fa8fb28df3a318c2371619eb8a3"
    );
}

#[test]
fn mgso_unknown_semantic_types_survive_byte_exact_round_trip() {
    let encoded = golden();
    let decoded = SemanticObject::decode(&encoded, 1024).unwrap();
    assert_eq!(decoded.type_id, "unknown.example");
    assert_eq!(decoded.interfaces, vec!["a", "z"]);
    assert_eq!(decoded.payload, vec![0xde, 0xad]);
    assert_eq!(decoded.encode().unwrap(), encoded);
}

#[test]
fn mgso_decoder_rejects_noncanonical_interfaces_and_trailing_data() {
    let mut unordered = golden();
    unordered[37] = b'z';
    unordered[42] = b'a';
    assert!(SemanticObject::decode(&unordered, 1024).is_err());

    let mut duplicate = golden();
    duplicate[42] = b'a';
    assert!(SemanticObject::decode(&duplicate, 1024).is_err());

    let mut extra = golden();
    extra.push(0);
    assert!(SemanticObject::decode(&extra, 1024).is_err());
}

#[test]
fn mgso_decoder_rejects_truncation_oversized_payload_and_malformed_text() {
    assert!(SemanticObject::decode(&golden()[..48], 1024).is_err());
    assert!(SemanticObject::decode(&golden(), 1).is_err());

    let mut invalid_utf8 = golden();
    invalid_utf8[10] = 0xff;
    assert!(SemanticObject::decode(&invalid_utf8, 1024).is_err());

    let mut huge_count = golden();
    huge_count[29..33].copy_from_slice(&u32::MAX.to_be_bytes());
    assert!(SemanticObject::decode(&huge_count, 1024).is_err());

    let mut huge_payload = golden();
    huge_payload[43..51].copy_from_slice(&u64::MAX.to_be_bytes());
    assert!(SemanticObject::decode(&huge_payload, 1024).is_err());

    let mut no_magic = golden();
    no_magic[0] = 0;
    assert!(SemanticObject::decode(&no_magic, 1024).is_err());
}

#[test]
fn mgso_encoder_refuses_empty_identifiers() {
    let mut empty_type = sample();
    empty_type.type_id.clear();
    assert!(empty_type.encode().is_err());

    let mut empty_interface = sample();
    empty_interface.interfaces.push(String::new());
    assert!(empty_interface.encode().is_err());
}
