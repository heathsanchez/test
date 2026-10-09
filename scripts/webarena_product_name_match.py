#!/usr/bin/env python3
"""Select a uniquely observed catalog product from a natural-language name.

A customer may name a product by a distinctive shortened prefix or ordered
model descriptors. Never choose between multiple matching variants.
"""
from __future__ import annotations
import json
import re


def compact(value):
    return ''.join(re.findall(r'[a-z0-9]+', str(value).casefold()))


def tokens(value):
    return re.findall(r'[a-z0-9]+',str(value).casefold())


def ordered_name_match(wanted, observed):
    expected=tokens(wanted)
    if len(expected)<3:
        return False
    available=iter(tokens(observed))
    return all(any(value==part for part in available) for value in expected)


def select_observed_product(wanted, candidates):
    if not isinstance(candidates,list) or not compact(wanted):
        raise RuntimeError('invalid product search observations')
    valid=[row for row in candidates if isinstance(row,dict)
           and row.get('name') and row.get('url')]
    exact=[row for row in valid if compact(row['name'])==compact(wanted)]
    if len(exact)==1:
        return exact[0]
    if len(exact)>1:
        raise RuntimeError('multiple exact catalog matches; product identity unknown')
    ordered=[row for row in valid if ordered_name_match(wanted,row['name'])]
    if len(ordered)==1:
        return ordered[0]
    raise RuntimeError('catalog product identity ambiguous or missing: '+json.dumps({
        'requested':wanted,
        'number_of_matches':len(ordered),
        'candidate_names':[row['name'] for row in ordered[:10]],
    },ensure_ascii=False))
