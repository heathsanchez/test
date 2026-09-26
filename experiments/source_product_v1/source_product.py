"""Exact unrestricted source/endpoint common-tail normalization.

No termination, finite quotient, Farey gap, or coefficient-contraction premise
is used. All arithmetic is integer arithmetic. The trace retains the fixed
original source and the complete affine cocycle.
"""
from dataclasses import dataclass, asdict
import json


def shortcut(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3*n+1)//2


@dataclass(frozen=True)
class Product:
    source: int
    depth: int
    odd_steps: int
    tail: int
    source_residue: int
    source_scale: int
    endpoint_residue: int
    endpoint_scale: int
    intercept: int

    @property
    def endpoint(self) -> int:
        return self.endpoint_residue + self.endpoint_scale*self.tail

    def valid(self) -> bool:
        return (self.source > 0 and self.depth >= 0 and self.odd_steps >= 0
                and self.tail >= 0 and self.intercept >= 0
                and self.source_scale == 2**self.depth
                and self.endpoint_scale == 3**self.odd_steps
                and 0 <= self.source_residue < self.source_scale
                and 0 <= self.endpoint_residue < self.endpoint_scale
                and self.source == self.source_residue+self.source_scale*self.tail
                and self.source_scale*self.endpoint_residue
                    == self.endpoint_scale*self.source_residue+self.intercept)


def initial(n: int) -> Product:
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError('source must be a positive integer')
    return Product(n, 0, 0, n, 0, 1, 0, 1, 0)


def advance(s: Product) -> Product:
    if not s.valid():
        raise ValueError('invalid source-product state')
    b = s.tail % 2
    v = s.endpoint_residue+s.endpoint_scale*b
    odd = v % 2
    t = Product(
        source=s.source, depth=s.depth+1, odd_steps=s.odd_steps+odd,
        tail=s.tail//2,
        source_residue=s.source_residue+s.source_scale*b,
        source_scale=2*s.source_scale,
        endpoint_residue=shortcut(v),
        endpoint_scale=(3 if odd else 1)*s.endpoint_scale,
        intercept=(3*s.intercept+s.source_scale if odd else s.intercept),
    )
    if not t.valid() or t.endpoint != shortcut(s.endpoint):
        raise ArithmeticError('source-product transition violated its invariant')
    return t


def normalize(n: int, depth: int) -> Product:
    if not isinstance(depth, int) or depth < 0:
        raise ValueError('depth must be a nonnegative integer')
    s = initial(n)
    for _ in range(depth):
        s = advance(s)
    return s


if __name__ == '__main__':
    a = normalize(27, 5)
    b = advance(a)
    print(json.dumps({
        'schema': 'COLLATZ_UNRESTRICTED_SOURCE_PRODUCT_V1',
        'tail_rank_separator': [asdict(a), asdict(b)],
        'endpoints': [a.endpoint, b.endpoint],
        'formal_source': 'formal/Collatz/SourceProduct.lean',
        'formal_affine_source': 'formal/Collatz/SourceProductAffine.lean',
        'proof_authority': 'Pinned Lean workflow, not this Python output',
        'compact_farey_projection': 'UNKNOWN',
        'residual_rank': 'UNKNOWN',
        'global_collatz': 'UNKNOWN',
    }, indent=2))
