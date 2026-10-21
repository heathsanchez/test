#!/usr/bin/env python3
"""Controlled native SQLite consequence separation. Does not establish general semantics."""
import sqlite3, re, json
from pathlib import Path

SCHEMAS = [
 ('measurements','amount','CREATE TABLE measurements(id INTEGER PRIMARY KEY, amount INTEGER NOT NULL CHECK (policy_ok(amount) = 1))'),
 ('orders','quantity','CREATE TABLE orders(id INTEGER PRIMARY KEY, quantity INTEGER NOT NULL CHECK (policy_ok(quantity) = 1))'),
]
REQUIREMENT = {'id':'SOURCE_REQUIREMENT_1','semantic_rule':'negative_value_must_be_rejected',
  'source':'researcher-authored independent synthetic requirement, not upstream author'}
def setup(schema, mode):
    _,_,ddl=schema
    db=sqlite3.connect(':memory:')
    db.create_function('policy_ok',1,lambda x: int(x>=0) if mode=='compliant' else 1,deterministic=False)
    db.execute(ddl)
    return db
def passive(db):
    return (tuple(db.execute("SELECT type,name,sql FROM sqlite_master ORDER BY name")),
            tuple(db.execute("PRAGMA foreign_keys")),
            tuple(db.execute("PRAGMA ignore_check_constraints")))
def compile_obligation(snapshot, policy):
    if policy is None: return {'status':'UNKNOWN_NO_AUTHORITY'}
    if policy.get('semantic_rule')!='negative_value_must_be_rejected':
        return {'status':'UNKNOWN_UNSUPPORTED_REQUIREMENT'}
    tables=[r for r in snapshot[0] if r[0]=='table']
    if len(tables)!=1: return {'status':'UNKNOWN_TABLE_COUNT'}
    _,name,ddl=tables[0]
    m=re.fullmatch(r'CREATE TABLE ([a-z_]+)\(id INTEGER PRIMARY KEY, ([a-z_]+) INTEGER NOT NULL CHECK \(policy_ok\(\2\) = 1\)\)',ddl)
    if not m or m.group(1)!=name: return {'status':'UNKNOWN_SCHEMA_LANGUAGE'}
    return {'status':'ADMISSIBLE','table':name,'column':m.group(2),'value':-1,
      'authority':'schema CHECK + separately supplied synthetic normative requirement'}
def intervene(db,op):
    assert op['status']=='ADMISSIBLE'
    table=op['table']; col=op['column']
    before=db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
    db.execute('SAVEPOINT protected_probe')
    try:
        db.execute('INSERT INTO '+table+' ('+col+') VALUES (?)',(op['value'],))
        result='VIOLATION_ACCEPTED'
    except sqlite3.IntegrityError:
        result='VIOLATION_REJECTED'
    finally:
        db.execute('ROLLBACK TO protected_probe')
        db.execute('RELEASE protected_probe')
    after=db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
    assert before==after
    return {'result':result,'row_count_preserved':True}
def trial(schema):
    compliant=setup(schema,'compliant')
    noncompliant=setup(schema,'noncompliant')
    try:
        s1=passive(compliant); s2=passive(noncompliant)
        assert s1==s2, 'not a passive indistinguishability example'
        op=compile_obligation(s1,REQUIREMENT)
        assert op['status']=='ADMISSIBLE',op
        a=intervene(compliant,op); b=intervene(noncompliant,op)
        assert a['result']=='VIOLATION_REJECTED'
        assert b['result']=='VIOLATION_ACCEPTED'
        assert compile_obligation(s1,None)['status']=='UNKNOWN_NO_AUTHORITY'
        assert compile_obligation(s1,REQUIREMENT)==op
        return {'schema':schema[0], 'passive_equivalent':True,
          'compiled_obligation':op, 'compliant_native':a, 'noncompliant_native':b,
          'withdrawal':'UNKNOWN','restoration':'PASS',
          'passive_only_baseline':'UNKNOWN',
          'fully_informed_intervention_baseline':'TIE (same negative insert permitted)'}
    finally:
        compliant.close();noncompliant.close()
def main():
    results=[trial(schema) for schema in SCHEMAS]
    out={'status':'WARRANTED_BOUNDED_CONTROLLED_SEPARATING_WITNESS',
      'cases':results,'scope':'two controlled native SQLite schemas and synthetic normative source',
      'R7_CLC_MATHGRAPH':'not invoked; independently verified earlier interfaces remain unchanged',
      'advantages':'no advantage vs fully informed intervention-capable baseline',
      'limitations':['synthetic independent requirement, not an external author',
        'opaque native user-function excluded from passive observation vocabulary',
        'one witness does not prove general constraint correctness',
        'no source-distinct prospective transfer or real cost advantage']}
    Path(__file__).with_name('result.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'trials':len(results),
      'passive_equal':all(r['passive_equivalent'] for r in results),
      'rejections':[r['compliant_native']['result'] for r in results],
      'violations':[r['noncompliant_native']['result'] for r in results],
      'baseline':'TIE'}))
if __name__=='__main__':main()
