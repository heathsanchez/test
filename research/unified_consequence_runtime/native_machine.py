"""Minimal native integration of the ORIGINAL MSI quotient and Metatron warrant log.

The observer is supplied by the caller. This is an executable integration
boundary, NOT autonomous observation/constructor invention. No invented scores.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Hashable

# Both imports resolve to pinned ORIGINAL upstream source in qualification CI.
from consequential_core import EquivalenceRelation
from metatron.nucleus import Node, append, dumps, loads, live_ids

@dataclass(frozen=True)
class ObservationCapability:
    name: str
    source: str
    scope: str
    implementation_sha256: str
    verifier: str

    def __post_init__(self):
        if not all((self.name, self.source, self.scope, self.implementation_sha256, self.verifier)):
            raise ValueError("missing scoped capability authority")

class Machine:
    def __init__(self, carrier, baseline: Callable, log=()):
        self.carrier=tuple(carrier)
        if not self.carrier or len(set(self.carrier)) != len(self.carrier):
            raise ValueError("carrier must be nonempty and distinct")
        self.baseline=baseline
        self.log=log
        self.capabilities={}
        self.observers={}

    def admit_observation(self, cap: ObservationCapability, observe: Callable, expected: dict, supersedes=None):
        if cap.name in self.capabilities:
            raise ValueError("capability already admitted")
        actual={str(x): observe(x) for x in self.carrier}
        if actual != expected:
            raise ValueError("independent observation contract disagrees")
        base=EquivalenceRelation.from_observation(self.carrier, self.baseline)
        # Use ORIGINAL MSI equivalence construction and its refinement order.
        combined=EquivalenceRelation.from_observation(self.carrier,
                         lambda x: (self.baseline(x), observe(x)))
        if not combined.refines(base):
            raise ValueError("observation did not lawfully refine old quotient")
        witness=any(base.same(x,y) and not combined.same(x,y)
                    for x in self.carrier for y in self.carrier)
        if not witness:
            raise ValueError("observation adds no consequential distinction")
        source=append(self.log,Node("source",{"source":cap.source,"scope":cap.scope,
                 "implementation_sha256":cap.implementation_sha256,\n                 "supersedes":supersedes}))
        evidence=append(source,Node("independent_observation",{
            "verifier":cap.verifier,"expected_sha256":sha256(
              json.dumps(expected,sort_keys=True).encode()).hexdigest()},
            premises=(source[-1].id,)))
        capability=Node("capability",{"name":cap.name,"scope":cap.scope,
              "source":cap.source},premises=(evidence[-1].id,))
        self.log=append(evidence,capability)
        self.capabilities[cap.name]=capability.id
        self.observers[cap.name]=observe
        return {"capability_id":capability.id,"refined":True,
                "strict_witness":witness}

    def equivalent(self,x,y):
        if x not in self.carrier or y not in self.carrier:
            raise ValueError("outside carrier")
        active=set(live_ids(self.log))
        old=self.baseline(x)==self.baseline(y)
        if not old: return False
        return all(obs(x)==obs(y) for name,obs in self.observers.items()
                   if self.capabilities[name] in active)

    def withdraw(self,name):
        target=self.capabilities[name]
        self.log=append(self.log,Node("revoke",{"target":target,
                              "reason":"controlled source-support withdrawal"}))

    def restore_from_original_support(self,name,cap,observe,expected):
        # Restoration must use a new source/receipt, never un-revoke old evidence.
        self.capabilities.pop(name)
        self.observers.pop(name)
        return self.admit_observation(cap,observe,expected)

    def persist(self,path):
        Path(path).write_text(dumps(self.log))

    @classmethod
    def reload(cls,path,carrier,baseline,capabilities,observers):
        machine=cls(carrier,baseline,loads(Path(path).read_text()))
        machine.capabilities=dict(capabilities)
        machine.observers=dict(observers)
        return machine
