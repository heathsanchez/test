#!/usr/bin/env python3
"""Posthoc AnyIO V104 pre-cap source-observer applicability test.

Uses the already-qualified original V13 guard extractor and the byte-pinned
ORIGINAL V104 generator. A new general lexical relevance scorer is human-authored
for this exposed diagnostic, and is NOT a prospectively acquired operation.
No native candidate tests, repaired original source, or sealed future reading.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import keyword
import math
import re
import sys
import textwrap
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

from research.unified_consequence_runtime import observed_branch_v13 as v13
from research.unified_consequence_runtime.qualify_recursive_frontier import original_candidates

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT/"research/unified_consequence_runtime/G2_ANYIO_PRECAP_DIAGNOSTIC_PROTOCOL_V1.json"
SHA = lambda b: hashlib.sha256(b).hexdigest()
NAMERE = re.compile(r"[A-Za-z_]\w*\Z")

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def tokens(node):
    result=set()
    for part in ast.walk(node):
        if isinstance(part,ast.Name):result.add(part.id)
        if isinstance(part,ast.Attribute):result.add(part.attr)
        if isinstance(part,ast.Import):
            result.update(piece for name in part.names for piece in name.name.split("."))
        if isinstance(part,ast.ImportFrom) and part.module:
            result.update(part.module.split("."))
        if isinstance(part,ast.arg):result.add(part.arg)
        if isinstance(part,ast.Constant) and isinstance(part.value,str) and NAMERE.fullmatch(part.value):
            result.add(part.value)
    return {x for x in result if NAMERE.fullmatch(x) and not keyword.iskeyword(x) and not x.startswith("_")}

def embedded_test_symbols(test_source,expected):
    tr=ast.parse(test_source)
    matches=[n for n in tr.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
             and n.name in expected]
    if len(matches)!=len(expected) or {f.name for f in matches}!=set(expected):
        raise ValueError("FROZEN_PROTECTED_TEST_NOT_PRESENT")
    bags=[]
    for f in matches:
        terms=set()
        for x in ast.walk(f):
            if isinstance(x,ast.Constant) and isinstance(x.value,str):
                inner=textwrap.dedent(x.value)
                if inner.lstrip().startswith(("import ","from ")):
                    try:terms.update(tokens(ast.parse(inner)))
                    except SyntaxError:raise ValueError("AUTHOR_TEST_EMBEDDED_SOURCE_NOT_PYTHON")
        if not terms:raise ValueError("NO_EMBEDDED_PROTECTED_SOURCE")
        bags.append(terms)
    return bags

def score_functions(source,termsets):
    tree=ast.parse(source)
    fs=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
    if not fs:raise ValueError("NO_ORIGINAL_FUNCTIONS")
    terms=set().union(*termsets)
    tok={node.name:tokens(node) for node in fs}
    freq=Counter(name for names in tok.values() for name in (names&terms))
    total=len(fs)
    scores=[]
    for node in fs:
        hit=sorted(tok[node.name]&terms)
        score=sum(math.log2((total+1)/(freq[x]+1)) for x in hit)
        scores.append(dict(name=node.name,line=node.lineno,source_terms=hit,score=round(score,9),
                           function_sha256=SHA(ast.dump(node,include_attributes=False).encode())))
    scores.sort(key=lambda x:(-x["score"],x["line"],x["name"]))
    return tree,fs,scores

def check_candidate_substitution(tree,function_name,changed_source):
    mutation=ast.parse(changed_source)
    if len(mutation.body)!=1 or not isinstance(mutation.body[0],(ast.FunctionDef,ast.AsyncFunctionDef)):
        return None
    if mutation.body[0].name!=function_name:return None
    changed=copy.deepcopy(tree)
    original=[i for i,f in enumerate(changed.body)
              if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.name==function_name]
    if len(original)!=1:raise ValueError("AMBIGUOUS_ORIGINAL_FUNCTION")
    before=changed.body[original[0]]
    replacement=mutation.body[0]
    if ast.dump(before,include_attributes=False)==ast.dump(replacement,include_attributes=False):
        return None
    changed.body[original[0]]=replacement
    before_others=[ast.dump(x,include_attributes=False) for i,x in enumerate(tree.body) if i!=original[0]]
    after_others=[ast.dump(x,include_attributes=False) for i,x in enumerate(changed.body) if i!=original[0]]
    assert before_others==after_others, "WRONG_AST_CHANGED"
    rendered=ast.unparse(ast.fix_missing_locations(changed))
    assert ast.dump(ast.parse(rendered),include_attributes=False)==ast.dump(changed,include_attributes=False)
    return SHA(rendered.encode())

def run(archive,v104_git):
    p=json.loads(PROTOCOL.read_text())
    pin=p["source_authority"]
    zipraw=Path(archive).read_bytes()
    if SHA(zipraw)!=pin["original_zip_sha256"]:raise ValueError("FROZEN_ORIGINAL_NATIVE_ARCHIVE_SHA_CHANGED")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError("ARCHIVE_CRC_FAILED")
        raw=z.read(pin["source_archive_path"]);author=z.read(pin["author_archive_path"])
        if SHA(raw)!=pin["source_sha256"] or git_blob(raw)!=pin["source_git_blob"]:
            raise ValueError("WRONG_SOURCE_BYTES")
        if SHA(author)!=pin["author_sha256"] or git_blob(author)!=pin["author_git_blob"]:
            raise ValueError("WRONG_AUTHOR_TEST_BYTES")
        cat=json.loads(z.read(pin["original_catalog_path"]))
    canonical=json.dumps(cat,sort_keys=True,separators=(",",":")).encode()
    if SHA(canonical)!=pin["original_catalog_canonical_sha256"]:
        raise ValueError("WRONG_ORIGINAL_SOURCE_ONLY_CATALOG")
    original_slots={tuple(x["changed_lines"]) for x in cat["rows"]}
    assert len(cat["rows"])==64 and original_slots=={(108,)}
    original_locations={x["path"] for x in cat["rows"]}
    assert original_locations=={"src/anyio/pytest_plugin.py"}
    source=raw.decode("utf-8");tests=author.decode("utf-8")
    original_guard_nodes=v13.guard_nodes("src/anyio/pytest_plugin.py",raw)
    obs=embedded_test_symbols(tests,p["selected_protected_test_names"])
    tree,fs,scores=score_functions(source,obs)
    cap=p["evaluation"]["max_selected_functions"]
    top=scores[:cap]
    if len(top)!=cap or not all(x["score"]>0 for x in top):
        raise ValueError("INSUFFICIENT_EVIDENCE_RELEVANT_SOURCE_LOCI")
    if any(x["name"]=="_is_auto_mode" for x in top):
        raise ValueError("NO_LOCALITY_CHANGED_FROM_ORIGINAL_CAP")
    # Source-input ablation: deliberately suppress the most informative protected
    # symbols; scores must change, but ablation does not establish causal repair.
    most_rare=sorted(set().union(*obs)-{"pytest","mark","anyio"})
    ablated=[x-set(most_rare) for x in obs]
    _,_,control=score_functions(source,ablated)
    if control==scores:raise ValueError("FROZEN_SOURCE_SYMBOL_ABLATION_NO_EFFECT")
    # Unmodified native V104 generator applied to selected function fragments.
    # Embed in original AST only after AST-equivalence of all untouched top-level nodes.
    constructions=[]
    for item in top:
        node=next(x for x in fs if x.name==item["name"])
        fragment=ast.unparse(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]))
        proposals=original_candidates(v104_git,fragment,cap=p["evaluation"]["max_emitted_per_selected_function"])
        valid=[]
        for sel,builder,new in proposals:
            sh=check_candidate_substitution(tree,item["name"],new)
            if sh:
                valid.append(dict(selector=list(sel),builder=list(builder),whole_program_sha256=sh))
        constructions.append(dict(function=item["name"],line=item["line"],
                                  original_emitted=len(proposals),
                                  valid_reembedded=len(valid),first_four=valid[:4]))
    # Preserve horizon-relative equivalence of MSI policies; do not declare new winner.
    groups=defaultdict(list)
    for name,order in cat["orders"].items():
        groups[tuple(order[:8])].append(name)
    sizes=sorted(len(names) for names in groups.values())
    if sizes!=[1,36]:raise ValueError("FROZEN_POLICY_SIGNATURE_DIFFERS")
    choice={
        "number_named_policies":len(cat["orders"]),
        "number_observationally_distinct_prefix_classes":len(groups),
        "prefix_class_sizes":sizes,
        "validity":"IDENTICAL_PREFIX_IMPLIES_IDENTICAL_RESULT_FOR_ALL_NATIVE_OUTCOMES",
        "selected_named_noncold":None,
        "selection_gate_v1":"IMPOSSIBLE_UNIQUE_NAMED_NONCOLD",
        "replacement_policy_qualification":"NOT_EXECUTED",
    }
    return {
        "classification":"WARRANTED_POSTHOC_SOURCE_ONLY_DIAGNOSTIC_NOT_G2",
        "original_archive_sha256":SHA(zipraw),"original_catalog_sha256":SHA(canonical),
        "method":"PREEXISTING_V13_GUARD_INVENTORY_PLUS_HUMAN_AUTHORED_GENERIC_SYMBOL_LINK",
        "native_observation_calls":0,
        "native_candidate_verifications":0,
        "existing_v13_guard_count":len(original_guard_nodes),
        "existing_v13_status":("NOT_APPLICABLE_NO_IF_NOT_SELF_GUARDS" if not original_guard_nodes
                                else "STATIC_GUARDS_ONLY_NEED_NATIVE_OBSERVATION"),
        "protected_embedded_symbols":sorted(set().union(*obs)),
        "original_source_locus":{"function":"_is_auto_mode","line":108,
                                 "catalog_candidates":64},
        "ranked_functions":scores,
        "new_pre_cap_top":top,
        "negative_ablation_ranking_changed":control[:cap]!=top,
        "negative_ablation_top":control[:cap],
        "v104_unchanged_source_reused":pin["v104_original_source"],
        "new_production_operations":constructions,
        "policy_quotient":choice,
        "heldout_future":"SEALED_UNOPENED",
        "G2":"UNKNOWN",
        "claims_not_supported":["native repaired AnyIO","prospective G2","new generator language",
                                 "unique historical cause","superiority to informed baseline"],
    }

def main():
    if len(sys.argv)!=4:raise SystemExit("usage: script FROZEN_ARTIFACT_ZIP PINNED_V104_GIT_DIR NEW_OUTPUT_DIR")
    target=Path(sys.argv[3])
    target.mkdir(parents=True,exist_ok=False)
    outcome=run(sys.argv[1],sys.argv[2])
    (target/"RESULT.json").write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:outcome.get(k) for k in (
        "classification","existing_v13_guard_count","new_pre_cap_top",
        "new_production_operations","policy_quotient","heldout_future","G2"
    )},indent=2))
if __name__=="__main__":main()
