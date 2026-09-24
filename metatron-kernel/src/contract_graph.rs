//! Diagnostic-only semantic contract graph.
//!
//! This module is intentionally excluded from ordinary release semantics.
//! It models independently qualified kernel capabilities as contracts over
//! semantic interfaces, then computes consequence closure without changing
//! checker behavior.

use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ContractStatus {
    Warranted,
    Candidate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SemanticContract {
    pub(crate) id: &'static str,
    pub(crate) status: ContractStatus,
    pub(crate) requires: &'static [&'static str],
    pub(crate) produces: &'static [&'static str],
    pub(crate) preserves: &'static [&'static str],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct AdapterContract {
    pub(crate) id: String,
    pub(crate) source: &'static str,
    pub(crate) target: &'static str,
    pub(crate) status: ContractStatus,
    pub(crate) preserves: BTreeSet<&'static str>,
    pub(crate) assumptions: BTreeSet<&'static str>,
    pub(crate) evidence: BTreeSet<&'static str>,
    pub(crate) provenance: Vec<&'static str>,
    is_identity: bool,
}

impl AdapterContract {
    pub(crate) fn atomic(
        id: &'static str,
        source: &'static str,
        target: &'static str,
        status: ContractStatus,
        preserves: impl IntoIterator<Item = &'static str>,
        assumptions: impl IntoIterator<Item = &'static str>,
        evidence: impl IntoIterator<Item = &'static str>,
    ) -> Self {
        Self {
            id: id.to_owned(),
            source,
            target,
            status,
            preserves: preserves.into_iter().collect(),
            assumptions: assumptions.into_iter().collect(),
            evidence: evidence.into_iter().collect(),
            provenance: vec![id],
            is_identity: false,
        }
    }

    pub(crate) fn identity(type_id: &'static str) -> Self {
        Self {
            id: format!("identity:{type_id}"),
            source: type_id,
            target: type_id,
            status: ContractStatus::Warranted,
            preserves: BTreeSet::new(),
            assumptions: BTreeSet::new(),
            evidence: BTreeSet::new(),
            provenance: Vec::new(),
            is_identity: true,
        }
    }
}

pub(crate) fn compose_adapter_contracts(
    first: &AdapterContract,
    second: &AdapterContract,
) -> Option<AdapterContract> {
    if first.target != second.source {
        return None;
    }
    if first.is_identity {
        return Some(second.clone());
    }
    if second.is_identity {
        return Some(first.clone());
    }

    let preserves = first
        .preserves
        .intersection(&second.preserves)
        .copied()
        .collect::<BTreeSet<_>>();
    let assumptions = first
        .assumptions
        .union(&second.assumptions)
        .copied()
        .collect::<BTreeSet<_>>();
    let evidence = first
        .evidence
        .union(&second.evidence)
        .copied()
        .collect::<BTreeSet<_>>();

    let mut provenance = first.provenance.clone();
    provenance.extend(second.provenance.iter().copied());
    let status = if first.status == ContractStatus::Warranted
        && second.status == ContractStatus::Warranted
    {
        ContractStatus::Warranted
    } else {
        ContractStatus::Candidate
    };

    Some(AdapterContract {
        id: format!("compose:{}", provenance.join(">")),
        source: first.source,
        target: second.target,
        status,
        preserves,
        assumptions,
        evidence,
        provenance,
        is_identity: false,
    })
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ProtectedSemanticState {
    pub(crate) type_id: &'static str,
    pub(crate) observations: BTreeMap<&'static str, i64>,
}

#[derive(Clone)]
pub(crate) struct ExecutableAdapter {
    pub(crate) contract: AdapterContract,
    stages: Vec<fn(ProtectedSemanticState) -> ProtectedSemanticState>,
}

impl ExecutableAdapter {
    pub(crate) fn atomic(
        contract: AdapterContract,
        stage: fn(ProtectedSemanticState) -> ProtectedSemanticState,
    ) -> Self {
        Self {
            contract,
            stages: vec![stage],
        }
    }

    pub(crate) fn identity(type_id: &'static str) -> Self {
        Self {
            contract: AdapterContract::identity(type_id),
            stages: Vec::new(),
        }
    }

    pub(crate) fn execute(&self, mut state: ProtectedSemanticState) -> ProtectedSemanticState {
        assert_eq!(state.type_id, self.contract.source);
        for stage in &self.stages {
            state = stage(state);
        }
        assert_eq!(state.type_id, self.contract.target);
        state
    }
}

pub(crate) fn compose_executable_adapters(
    first: &ExecutableAdapter,
    second: &ExecutableAdapter,
) -> Option<ExecutableAdapter> {
    let contract = compose_adapter_contracts(&first.contract, &second.contract)?;
    if first.contract.is_identity {
        return Some(second.clone());
    }
    if second.contract.is_identity {
        return Some(first.clone());
    }
    let mut stages = first.stages.clone();
    stages.extend(second.stages.iter().copied());
    Some(ExecutableAdapter { contract, stages })
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum ProtectedQuery {
    Value(i64),
    UnknownOutsidePreservationContract,
}

pub(crate) fn query_protected(
    adapter: &ExecutableAdapter,
    state: &ProtectedSemanticState,
    observation: &'static str,
) -> ProtectedQuery {
    if !adapter.contract.preserves.contains(observation) {
        return ProtectedQuery::UnknownOutsidePreservationContract;
    }
    state
        .observations
        .get(observation)
        .copied()
        .map(ProtectedQuery::Value)
        .unwrap_or(ProtectedQuery::UnknownOutsidePreservationContract)
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum PathStatus {
    WarrantedPath {
        contracts: Vec<&'static str>,
    },
    CandidatePath {
        candidate_count: usize,
        contracts: Vec<&'static str>,
    },
    NoRegisteredPath,
}

pub(crate) fn plan_required_interface(
    required: &'static str,
    object_evidence: impl IntoIterator<Item = &'static str>,
) -> PathStatus {
    let mut interfaces = object_evidence.into_iter().collect::<BTreeSet<_>>();
    let mut best = BTreeMap::<&'static str, (usize, Vec<&'static str>)>::new();

    loop {
        let mut changed = false;
        for contract in CONTRACTS {
            let mut candidate_cost = usize::from(contract.status == ContractStatus::Candidate);
            let mut provenance = Vec::<&'static str>::new();
            let mut ready = true;

            for required_interface in contract.requires {
                if interfaces.contains(required_interface) {
                    continue;
                }
                let Some((cost, path)) = best.get(required_interface) else {
                    ready = false;
                    break;
                };
                candidate_cost = candidate_cost.saturating_add(*cost);
                provenance.extend(path.iter().copied());
            }
            if !ready {
                continue;
            }

            provenance.push(contract.id);
            provenance.sort_unstable();
            provenance.dedup();

            for produced in contract.produces {
                let replace = match best.get(produced) {
                    None => true,
                    Some((old_cost, old_path)) => {
                        candidate_cost < *old_cost
                            || (candidate_cost == *old_cost && provenance.len() < old_path.len())
                    }
                };
                if replace {
                    best.insert(produced, (candidate_cost, provenance.clone()));
                    interfaces.insert(produced);
                    changed = true;
                }
            }
        }
        if !changed {
            break;
        }
    }

    if interfaces.contains(required) && !best.contains_key(required) {
        return PathStatus::WarrantedPath {
            contracts: Vec::new(),
        };
    }

    match best.get(required) {
        Some((0, path)) => PathStatus::WarrantedPath {
            contracts: path.clone(),
        },
        Some((candidate_count, path)) => PathStatus::CandidatePath {
            candidate_count: *candidate_count,
            contracts: path.clone(),
        },
        None => PathStatus::NoRegisteredPath,
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SemanticObjectEnvelope {
    pub(crate) type_id: &'static str,
    pub(crate) contract_version: u32,
    pub(crate) canonical_payload_digest: &'static str,
    pub(crate) interfaces: BTreeSet<&'static str>,
}

impl SemanticObjectEnvelope {
    pub(crate) fn new(
        type_id: &'static str,
        contract_version: u32,
        canonical_payload_digest: &'static str,
        interfaces: impl IntoIterator<Item = &'static str>,
    ) -> Self {
        Self {
            type_id,
            contract_version,
            canonical_payload_digest,
            interfaces: interfaces.into_iter().collect(),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ClosureResult {
    pub(crate) interfaces: BTreeSet<&'static str>,
    pub(crate) fired_contracts: Vec<&'static str>,
}

pub(crate) const CONTRACTS: &[SemanticContract] = &[
    SemanticContract {
        id: "opaque.type-signature@1",
        status: ContractStatus::Warranted,
        requires: &["validated.type@1"],
        produces: &["type.signature@1"],
        preserves: &["lean.verdict@1"],
    },
    SemanticContract {
        id: "opaque.constructor-signature@1",
        status: ContractStatus::Warranted,
        requires: &["validated.constructor@1"],
        produces: &["constructor.signature@1"],
        preserves: &["lean.verdict@1"],
    },
    SemanticContract {
        id: "opaque.recursor-signature@1",
        status: ContractStatus::Warranted,
        requires: &["validated.recursor@1"],
        produces: &["recursor.signature@1"],
        preserves: &["lean.verdict@1"],
    },
    SemanticContract {
        id: "projection.spec@1",
        status: ContractStatus::Warranted,
        requires: &[
            "type.signature@1",
            "constructor.signature@1",
            "validated.projection-spec@1",
        ],
        produces: &["projection.type@1", "projection.reduce@1"],
        preserves: &["lean.verdict@1"],
    },
    SemanticContract {
        id: "recursor.iota@1",
        status: ContractStatus::Warranted,
        requires: &[
            "recursor.signature@1",
            "constructor.signature@1",
            "validated.recursor-rule@1",
        ],
        produces: &["recursor.iota@1"],
        preserves: &["lean.verdict@1"],
    },
    // Recent Nucleus evidence shows this operation is semantically useful
    // inside the recursor-signature proof, but it has not yet earned a whole
    // protected Arena verdict. It must therefore stay out of warranted closure.
    SemanticContract {
        id: "projection.reduce-then-apply@1",
        status: ContractStatus::Candidate,
        requires: &["projection.reduce@1", "application@1"],
        produces: &["projection.apply@1"],
        preserves: &["lean.verdict@1"],
    },
    // Developmental shadow contracts. These represent the recent interface
    // reclosure experiments and deliberately remain CANDIDATE until a protected
    // consequence is earned.
    SemanticContract {
        id: "structure.fields.shadow@1",
        status: ContractStatus::Candidate,
        requires: &[
            "type.signature@1",
            "constructor.signature@1",
            "recursor.signature@1",
            "validated.structure-shape@1",
        ],
        produces: &["structure.fields@1"],
        preserves: &["lean.verdict@1"],
    },
    SemanticContract {
        id: "indexed-recursive.shadow@1",
        status: ContractStatus::Candidate,
        requires: &[
            "type.signature@1",
            "constructor.signature@1",
            "recursor.signature@1",
            "validated.indexed-recursive-shape@1",
        ],
        produces: &["inductive.indexed-recursive@1"],
        preserves: &["lean.verdict@1"],
    },
    // Explicit negative control: a cost-only observation must never be inferred
    // from contracts qualified only for Lean verdict preservation.
    SemanticContract {
        id: "resource.cost.placeholder@1",
        status: ContractStatus::Candidate,
        requires: &["projection.reduce@1"],
        produces: &["resource.cost@1"],
        preserves: &["resource.cost@1"],
    },
];

pub(crate) fn close_interfaces(
    seeds: impl IntoIterator<Item = &'static str>,
    include_candidates: bool,
    protected_observation: &'static str,
) -> ClosureResult {
    let mut interfaces = seeds.into_iter().collect::<BTreeSet<_>>();
    let mut fired = BTreeSet::<&'static str>::new();

    loop {
        let mut changed = false;
        for contract in CONTRACTS {
            if fired.contains(contract.id)
                || (!include_candidates && contract.status != ContractStatus::Warranted)
                || !contract.preserves.contains(&protected_observation)
                || !contract
                    .requires
                    .iter()
                    .all(|required| interfaces.contains(required))
            {
                continue;
            }

            fired.insert(contract.id);
            for produced in contract.produces {
                changed |= interfaces.insert(produced);
            }
        }
        if !changed {
            break;
        }
    }

    ClosureResult {
        interfaces,
        fired_contracts: fired.into_iter().collect(),
    }
}

#[cfg(test)]
mod tests {
    use super::{
        AdapterContract, ContractStatus, ExecutableAdapter, ProtectedQuery, ProtectedSemanticState,
        SemanticObjectEnvelope, close_interfaces, compose_adapter_contracts,
        compose_executable_adapters, query_protected,
    };

    fn seed_interfaces() -> [&'static str; 9] {
        [
            "validated.type@1",
            "validated.constructor@1",
            "validated.recursor@1",
            "validated.projection-spec@1",
            "validated.recursor-rule@1",
            "validated.structure-shape@1",
            "validated.indexed-recursive-shape@1",
            "application@1",
            "canonical.payload@1",
        ]
    }

    #[test]
    fn object_envelope_preserves_unknown_future_semantics_without_reinterpretation() {
        let object = SemanticObjectEnvelope::new(
            "lean.inductive@1",
            1,
            "sha256:test-only-digest",
            ["canonical.payload@1", "type.signature@1"],
        );

        assert_eq!(object.type_id, "lean.inductive@1");
        assert_eq!(object.contract_version, 1);
        assert_eq!(object.canonical_payload_digest, "sha256:test-only-digest");
        assert!(object.interfaces.contains("canonical.payload@1"));
        assert!(object.interfaces.contains("type.signature@1"));
        assert!(!object.interfaces.contains("future.unknown-interface@1"));
    }

    #[test]
    fn warranted_closure_never_leaks_candidate_authority() {
        let closure = close_interfaces(seed_interfaces(), false, "lean.verdict@1");

        for interface in [
            "type.signature@1",
            "constructor.signature@1",
            "recursor.signature@1",
            "projection.type@1",
            "projection.reduce@1",
            "recursor.iota@1",
        ] {
            assert!(
                closure.interfaces.contains(interface),
                "missing {interface}"
            );
        }

        for candidate_only in [
            "projection.apply@1",
            "structure.fields@1",
            "inductive.indexed-recursive@1",
            "resource.cost@1",
        ] {
            assert!(
                !closure.interfaces.contains(candidate_only),
                "candidate leaked into warranted closure: {candidate_only}"
            );
        }
    }

    #[test]
    fn exploratory_closure_reconstructs_the_recent_interface_frontier() {
        let closure = close_interfaces(seed_interfaces(), true, "lean.verdict@1");

        for interface in [
            "projection.apply@1",
            "structure.fields@1",
            "inductive.indexed-recursive@1",
        ] {
            assert!(
                closure.interfaces.contains(interface),
                "exploratory closure did not recover {interface}"
            );
        }

        assert!(
            closure
                .fired_contracts
                .contains(&"projection.reduce-then-apply@1")
        );
        assert!(
            closure
                .fired_contracts
                .contains(&"structure.fields.shadow@1")
        );
        assert!(
            closure
                .fired_contracts
                .contains(&"indexed-recursive.shadow@1")
        );
    }

    #[test]
    fn preservation_contract_blocks_cross_observation_composition() {
        let lean = close_interfaces(seed_interfaces(), true, "lean.verdict@1");
        assert!(!lean.interfaces.contains("resource.cost@1"));

        let resource = close_interfaces(
            ["validated.type@1", "validated.projection-spec@1"],
            true,
            "resource.cost@1",
        );
        assert!(!resource.interfaces.contains("projection.reduce@1"));
        assert!(!resource.interfaces.contains("resource.cost@1"));
    }

    #[test]
    fn emits_deterministic_contract_closure_evidence() {
        let warranted = close_interfaces(seed_interfaces(), false, "lean.verdict@1");
        let exploratory = close_interfaces(seed_interfaces(), true, "lean.verdict@1");

        eprintln!(
            "NUCLEUS_CONTRACT_WARRANTED:interfaces={:?}:contracts={:?}",
            warranted.interfaces, warranted.fired_contracts
        );
        eprintln!(
            "NUCLEUS_CONTRACT_EXPLORATORY:interfaces={:?}:contracts={:?}",
            exploratory.interfaces, exploratory.fired_contracts
        );

        assert!(!warranted.interfaces.contains("projection.apply@1"));
        assert!(exploratory.interfaces.contains("projection.apply@1"));
    }

    fn retain_observations(
        mut state: ProtectedSemanticState,
        target: &'static str,
        retained: &[&'static str],
    ) -> ProtectedSemanticState {
        state
            .observations
            .retain(|observation, _| retained.contains(observation));
        state.type_id = target;
        state
    }

    fn source_to_middle(state: ProtectedSemanticState) -> ProtectedSemanticState {
        retain_observations(
            state,
            "kernel.middle@1",
            &[
                "lean.verdict@1",
                "lean.control-state@1",
                "lean.protected-result@1",
            ],
        )
    }

    fn middle_to_target(state: ProtectedSemanticState) -> ProtectedSemanticState {
        retain_observations(
            state,
            "kernel.target@1",
            &["lean.verdict@1", "lean.protected-result@1"],
        )
    }

    fn target_to_summary(state: ProtectedSemanticState) -> ProtectedSemanticState {
        retain_observations(
            state,
            "kernel.summary@1",
            &["lean.verdict@1", "lean.protected-result@1"],
        )
    }

    fn category_chain() -> (ExecutableAdapter, ExecutableAdapter, ExecutableAdapter) {
        let a = ExecutableAdapter::atomic(
            AdapterContract::atomic(
                "adapter.source-middle@1",
                "kernel.source@1",
                "kernel.middle@1",
                ContractStatus::Warranted,
                [
                    "lean.verdict@1",
                    "lean.control-state@1",
                    "lean.protected-result@1",
                ],
                ["lean.kernel-assumptions@1"],
                ["evidence:source-middle"],
            ),
            source_to_middle,
        );
        let b = ExecutableAdapter::atomic(
            AdapterContract::atomic(
                "adapter.middle-target@1",
                "kernel.middle@1",
                "kernel.target@1",
                ContractStatus::Warranted,
                ["lean.verdict@1", "lean.protected-result@1"],
                ["projection.contract@1"],
                ["evidence:middle-target"],
            ),
            middle_to_target,
        );
        let c = ExecutableAdapter::atomic(
            AdapterContract::atomic(
                "adapter.target-summary@1",
                "kernel.target@1",
                "kernel.summary@1",
                ContractStatus::Warranted,
                [
                    "lean.verdict@1",
                    "lean.protected-result@1",
                    "resource.cost@1",
                ],
                ["summary.contract@1"],
                ["evidence:target-summary"],
            ),
            target_to_summary,
        );
        (a, b, c)
    }

    fn source_state() -> ProtectedSemanticState {
        ProtectedSemanticState {
            type_id: "kernel.source@1",
            observations: [
                ("lean.verdict@1", 1),
                ("lean.control-state@1", 7),
                ("lean.protected-result@1", 42),
                ("resource.cost@1", 999),
            ]
            .into_iter()
            .collect(),
        }
    }

    #[test]
    fn preservation_of_composite_is_intersection_and_metadata_composes_structurally() {
        let (a, b, _) = category_chain();
        let ab = compose_adapter_contracts(&a.contract, &b.contract).expect("A then B composes");

        assert_eq!(ab.source, "kernel.source@1");
        assert_eq!(ab.target, "kernel.target@1");
        assert_eq!(ab.status, ContractStatus::Warranted);
        assert_eq!(
            ab.preserves,
            ["lean.protected-result@1", "lean.verdict@1"]
                .into_iter()
                .collect()
        );
        assert_eq!(
            ab.assumptions,
            ["lean.kernel-assumptions@1", "projection.contract@1"]
                .into_iter()
                .collect()
        );
        assert_eq!(
            ab.evidence,
            ["evidence:middle-target", "evidence:source-middle"]
                .into_iter()
                .collect()
        );
        assert_eq!(
            ab.provenance,
            vec!["adapter.source-middle@1", "adapter.middle-target@1"]
        );
    }

    #[test]
    fn adapter_composition_is_associative_at_contract_and_protected_output_levels() {
        let (a, b, c) = category_chain();

        let ab = compose_executable_adapters(&a, &b).expect("A then B");
        let left = compose_executable_adapters(&ab, &c).expect("(C o B) o A");

        let bc = compose_executable_adapters(&b, &c).expect("B then C");
        let right = compose_executable_adapters(&a, &bc).expect("C o (B o A)");

        assert_eq!(left.contract, right.contract);
        assert_eq!(
            left.contract.preserves,
            ["lean.protected-result@1", "lean.verdict@1"]
                .into_iter()
                .collect()
        );
        assert_eq!(
            left.contract.provenance,
            vec![
                "adapter.source-middle@1",
                "adapter.middle-target@1",
                "adapter.target-summary@1",
            ]
        );

        let source = source_state();
        let left_output = left.execute(source.clone());
        let right_output = right.execute(source);
        assert_eq!(left_output, right_output);
        assert_eq!(
            query_protected(&left, &left_output, "lean.protected-result@1"),
            ProtectedQuery::Value(42)
        );
        assert_eq!(
            query_protected(&right, &right_output, "lean.protected-result@1"),
            ProtectedQuery::Value(42)
        );
        assert_eq!(
            query_protected(&left, &left_output, "lean.control-state@1"),
            ProtectedQuery::UnknownOutsidePreservationContract
        );
        assert_eq!(
            query_protected(&right, &right_output, "resource.cost@1"),
            ProtectedQuery::UnknownOutsidePreservationContract
        );
    }

    #[test]
    fn identity_adapter_is_left_and_right_identity_for_contract_and_execution() {
        let (a, _, _) = category_chain();
        let source_identity = ExecutableAdapter::identity("kernel.source@1");
        let middle_identity = ExecutableAdapter::identity("kernel.middle@1");

        let left = compose_executable_adapters(&source_identity, &a).expect("A o I");
        let right = compose_executable_adapters(&a, &middle_identity).expect("I o A");

        assert_eq!(left.contract, a.contract);
        assert_eq!(right.contract, a.contract);

        let source = source_state();
        assert_eq!(left.execute(source.clone()), a.execute(source.clone()));
        assert_eq!(right.execute(source.clone()), a.execute(source));
    }

    #[test]
    fn candidate_status_contaminates_composite_without_leaking_warrant() {
        let (a, _, _) = category_chain();
        let candidate = ExecutableAdapter::atomic(
            AdapterContract::atomic(
                "adapter.candidate@1",
                "kernel.middle@1",
                "kernel.target@1",
                ContractStatus::Candidate,
                ["lean.verdict@1"],
                ["candidate.assumption@1"],
                ["evidence:candidate"],
            ),
            middle_to_target,
        );

        let composite =
            compose_executable_adapters(&a, &candidate).expect("candidate composition is defined");
        assert_eq!(composite.contract.status, ContractStatus::Candidate);
        assert_eq!(
            composite.contract.preserves,
            ["lean.verdict@1"].into_iter().collect()
        );
    }

    #[test]
    fn emits_categorical_contract_evidence() {
        let (a, b, c) = category_chain();
        let ab = compose_executable_adapters(&a, &b).expect("A then B");
        let left = compose_executable_adapters(&ab, &c).expect("left bracketing");
        let bc = compose_executable_adapters(&b, &c).expect("B then C");
        let right = compose_executable_adapters(&a, &bc).expect("right bracketing");
        let output = left.execute(source_state());

        eprintln!(
            "NUCLEUS_CATEGORY_ASSOCIATIVE:contract_equal={}:output_equal={}:preserves={:?}:assumptions={:?}:evidence={:?}:provenance={:?}",
            left.contract == right.contract,
            output == right.execute(source_state()),
            left.contract.preserves,
            left.contract.assumptions,
            left.contract.evidence,
            left.contract.provenance,
        );
        eprintln!(
            "NUCLEUS_CATEGORY_UNKNOWN:control={:?}:cost={:?}",
            query_protected(&left, &output, "lean.control-state@1"),
            query_protected(&left, &output, "resource.cost@1"),
        );

        assert_eq!(left.contract, right.contract);
        assert_eq!(output, right.execute(source_state()));
    }

    #[test]
    fn contract_status_is_explicit_not_inferred_from_presence() {
        let candidate = super::CONTRACTS
            .iter()
            .find(|contract| contract.id == "projection.reduce-then-apply@1")
            .expect("candidate exists");
        assert_eq!(candidate.status, ContractStatus::Candidate);
    }
}
