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
pub(crate) enum PathStatus {
    Warranted {
        contracts: Vec<&'static str>,
        path_id: String,
    },
    Candidate {
        candidate_count: usize,
        contracts: Vec<&'static str>,
        path_id: String,
    },
    None,
}

fn contract_registry_rank(id: &str) -> usize {
    CONTRACTS
        .iter()
        .position(|contract| contract.id == id)
        .unwrap_or(usize::MAX)
}

pub(crate) fn canonicalize_planner_lineage(
    contracts: impl IntoIterator<Item = &'static str>,
) -> Vec<&'static str> {
    let mut lineage = contracts
        .into_iter()
        .filter(|id| !id.starts_with("identity:"))
        .collect::<Vec<_>>();
    lineage.sort_by(|left, right| {
        contract_registry_rank(left)
            .cmp(&contract_registry_rank(right))
            .then_with(|| left.cmp(right))
    });
    lineage.dedup();
    lineage
}

pub(crate) fn canonical_planner_path_id(
    required: &'static str,
    candidate_count: usize,
    contracts: impl IntoIterator<Item = &'static str>,
) -> String {
    let lineage = canonicalize_planner_lineage(contracts);
    format!(
        "planner:{required}:c{candidate_count}:{}",
        lineage.join(">")
    )
}

pub(crate) fn canonical_adapter_path_id(contract: &AdapterContract) -> String {
    let lineage = contract
        .provenance
        .iter()
        .copied()
        .filter(|id| !id.starts_with("identity:"))
        .collect::<Vec<_>>();
    format!(
        "adapter:{}:{}:{}:{}",
        contract.source,
        contract.target,
        contract
            .preserves
            .iter()
            .copied()
            .collect::<Vec<_>>()
            .join(","),
        lineage.join(">")
    )
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
            provenance = canonicalize_planner_lineage(provenance);

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
        return PathStatus::Warranted {
            contracts: Vec::new(),
            path_id: canonical_planner_path_id(required, 0, []),
        };
    }

    match best.get(required) {
        Some((0, path)) => PathStatus::Warranted {
            contracts: path.clone(),
            path_id: canonical_planner_path_id(required, 0, path.iter().copied()),
        },
        Some((candidate_count, path)) => PathStatus::Candidate {
            candidate_count: *candidate_count,
            contracts: path.clone(),
            path_id: canonical_planner_path_id(required, *candidate_count, path.iter().copied()),
        },
        None => PathStatus::None,
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
    SemanticContract {
        id: "nat.beq.reflexive@1",
        status: ContractStatus::Warranted,
        requires: &["validated.nat-beq@1", "same.semantic-argument@1"],
        produces: &["bool.constructor.true@1"],
        preserves: &["lean.verdict@1"],
    },
    SemanticContract {
        id: "bool.recursor.true@1",
        status: ContractStatus::Warranted,
        requires: &[
            "validated.bool-recursor@1",
            "bool.constructor.true@1",
            "recursor.iota@1",
        ],
        produces: &["bool.recursor.true-consequence@1"],
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
    use super::{ContractStatus, close_interfaces};

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

    #[test]
    fn contract_status_is_explicit_not_inferred_from_presence() {
        let candidate = super::CONTRACTS
            .iter()
            .find(|contract| contract.id == "projection.reduce-then-apply@1")
            .expect("candidate exists");
        assert_eq!(candidate.status, ContractStatus::Candidate);
    }
}
