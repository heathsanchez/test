"""Source-pinned official Lean differential cases for a two-owner record.

All mutations retain the unchanged source prefix. The authentic input and
renaming are positive controls; metadata forgeries are negative controls.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path


SOURCE_SHA = 'f37e9434b2cee5f9623a2218fb6418c58d43dbe5ac3582cadd9cc844dfa215b4'
TARGET = 13129


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--source', type=Path, required=True)
    cli.add_argument('--out', type=Path, required=True)
    args = cli.parse_args()
    data = args.source.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SOURCE_SHA
    lines = data.splitlines(keepends=True)
    rows = [json.loads(line) for line in lines]
    original = rows[-1]['inductive']
    assert len(original['types']) == len(original['ctors']) == len(original['recs']) == 1
    assert original['types'][0]['name'] == TARGET
    assert len(original['types'][0]['levelParams']) == 2
    names = {r['in']:r for r in rows if 'in' in r}
    levels = {r['il']:r for r in rows if 'il' in r}
    exprs = {r['ie']:r for r in rows if 'ie' in r}
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = []

    def full_name(idx):
        if idx == 0: return ''
        part = names[idx].get('str', names[idx].get('num'))
        return (full_name(part['pre']) + '.' + str(part.get('str',part.get('num')))).lstrip('.')

    print('TWO_OWNER_ORIGINAL', [full_name(i) for i in original['recs'][0]['levelParams']], flush=True)
    original_prefix = b''.join(lines[:-1])

    def emit(label, payload, additions, expected):
        result = original_prefix + b''.join((json.dumps(x,separators=(',',':'))+'\n').encode() for x in additions + [{'inductive':payload}])
        dest=args.out/(label+'.ndjson')
        dest.write_bytes(result)
        manifest.append({'case':label,'file':dest.name,
                         'sha256':hashlib.sha256(result).hexdigest(),
                         'expect_reference':expected})

    cases=[('original',None,None),
           ('fresh-w',None,'w'),('fresh-u3',None,'u_3'),
           ('hierarchical',None,'probe.u'),
           ('owners-renamed',['r','s'],None)]
    for label, owners, motive in cases:
        extra=[]
        by_name={full_name(i):i for i in names}
        next_n=[max(names)+1]
        next_l=[max(levels)+1]
        next_e=[max(exprs)+1]

        def name(value):
            if value in by_name: return by_name[value]
            parent,_,leaf=value.rpartition('.')
            pre=name(parent) if parent else 0
            idx=next_n[0]; next_n[0]+=1
            by_name[value]=idx
            extra.append({'in':idx,'str':{'pre':pre,'str':leaf}})
            return idx

        block=copy.deepcopy(original)
        oldowners=list(block['types'][0]['levelParams'])
        oldm=block['recs'][0]['levelParams'][0]
        mapping={}
        if owners is not None:
            newowners=[name(x) for x in owners]
            mapping.update(zip(oldowners,newowners))
            block['types'][0]['levelParams']=newowners
            block['ctors'][0]['levelParams']=newowners
        else:
            newowners=oldowners
        if motive:
            mapping[oldm]=name(motive)
        block['recs'][0]['levelParams']=[mapping.get(oldm,oldm),*newowners]
        changed_levels={}
        changed_exprs={}

        def level(idx):
            if idx == 0: return 0
            if idx in changed_levels: return changed_levels[idx]
            before=levels[idx]; obj=copy.deepcopy(before)
            if 'param' in obj:
                obj['param']=mapping.get(obj['param'],obj['param'])
            if 'succ' in obj:
                obj['succ']=level(obj['succ'])
            for tag in ('max','imax'):
                if tag in obj:
                    obj[tag]=[level(x)for x in obj[tag]]
            if obj == before:
                changed_levels[idx]=idx
                return idx
            fresh=next_l[0]; next_l[0]+=1
            obj['il']=fresh
            extra.append(obj)
            changed_levels[idx]=fresh
            return fresh

        def expr(idx):
            if idx in changed_exprs: return changed_exprs[idx]
            before=exprs[idx]; obj=copy.deepcopy(before)
            if 'sort' in obj:
                obj['sort']=level(obj['sort'])
            if 'const' in obj:
                obj['const']['us']=[level(x)for x in obj['const']['us']]
            if 'app' in obj:
                for key in ('fn','arg'):
                    obj['app'][key]=expr(obj['app'][key])
            for tag in ('lam','forallE','letE'):
                if tag in obj:
                    keys=('type','body','value') if tag=='letE' else ('type','body')
                    for key in keys:
                        obj[tag][key]=expr(obj[tag][key])
            if 'proj' in obj:
                obj['proj']['struct']=expr(obj['proj']['struct'])
            if obj == before:
                changed_exprs[idx]=idx
                return idx
            fresh=next_e[0]; next_e[0]+=1
            obj['ie']=fresh
            extra.append(obj)
            changed_exprs[idx]=fresh
            return fresh

        for declaration in block['types']+block['ctors']+block['recs']:
            declaration['type']=expr(declaration['type'])
        for recursor in block['recs']:
            for rule in recursor['rules']:
                rule['rhs']=expr(rule['rhs'])
        emit(label,block,extra,0 if label in ('original','owners-renamed') else 1)

    cases=[('forged-k-on',lambda b:b['recs'][0].__setitem__('k',True)),
           ('forged-field-count',lambda b:b['ctors'][0].__setitem__('numFields',2)),
           ('forged-recursor-owner',lambda b:b['recs'][0]['levelParams'].__setitem__(2,326)),
           ('forged-rule-fields',lambda b:b['recs'][0]['rules'][0].__setitem__('nfields',2)),
           ('forged-ctor-params',lambda b:b['ctors'][0].__setitem__('numParams',1))]
    for label, mutation in cases:
        block=copy.deepcopy(original)
        mutation(block)
        emit(label,block,[],1)
    (args.out/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert len(manifest) == 10


if __name__ == '__main__':
    main()
