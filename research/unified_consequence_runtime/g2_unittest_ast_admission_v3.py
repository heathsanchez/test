#!/usr/bin/env python3
"""Pure source-neutral test-node eligibility extension for unittest.TestCase.

Only classes confirmed by imported unittest.TestCase base or originally
supported Test* naming are traversed. Identical AST changed method selection.
"""
import ast
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as legacy

def testcases(raw):
    root=ast.parse(raw)
    unittest_class={"TestCase"}
    unittest_module={"unittest"}
    for node in root.body:
        if isinstance(node,ast.ImportFrom) and node.module=="unittest":
            for a in node.names:
                if a.name=="TestCase":unittest_class.add(a.asname or a.name)
        if isinstance(node,ast.Import):
            for a in node.names:
                if a.name=="unittest":unittest_module.add(a.asname or a.name)
    def allowed_class(node):
        if node.name.startswith("Test"): return True
        return any(
            (isinstance(b,ast.Name) and b.id in unittest_class) or
            (isinstance(b,ast.Attribute) and b.attr=="TestCase" and
             isinstance(b.value,ast.Name) and b.value.id in unittest_module)
            for b in node.bases)
    found={}
    def recurse(nodes,prefix):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test_"):
                found["::".join(prefix+[n.name])]=ast.dump(n,include_attributes=False)
            elif isinstance(n,ast.ClassDef) and allowed_class(n):
                recurse(n.body,prefix+[n.name])
    recurse(root.body,[])
    return found

def select_protected(base,head,path):
    a=testcases(base);b=testcases(head)
    return [path+"::"+n for n in sorted(b) if a.get(n)!=b[n]]

def controls():
    a=b"""from unittest import TestCase as UC
class SchedulerTests(UC):
    def test_existing(self): pass
class RandomFixture:
    def test_fake(self): pass
"""
    b=a.replace(b"def test_existing(self): pass",b"def test_existing(self): assert 1 == 1")
    assert select_protected(a,b,"test_unit.py")==["test_unit.py::SchedulerTests::test_existing"]
    assert not any("test_fake" in x for x in testcases(b))
    c=b"""import unittest as testlib
class ValidatorCases(testlib.TestCase):
    def test_one(self): pass
"""
    assert "ValidatorCases::test_one" in testcases(c)
    d=b"""class TestPytestStyle:
    def test_this(self): pass
"""
    assert "TestPytestStyle::test_this" in testcases(d)
    return {"unittest_alias":True,"pytest_class":True,"non_test_class_refused":True}

def install():
    # This operation changes only eligibility selection, not code/repair grammar.
    legacy.select_protected=select_protected
    return legacy
