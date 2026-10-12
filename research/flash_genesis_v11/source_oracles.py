"""V11 SOURCE families only. No protected imports or target ground-truth labels."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Family:
    name: str
    n: int
    independent: object
    kind: str

def bits(mask,n):return (i for i in range(n) if mask>>i&1)

def v10_knapsack():
    weights=(3,2,2,1,1,1)
    return Family('source_v10_knapsack',6,
                  lambda mask:sum(weights[i] for i in bits(mask,len(weights)))<=4,'hereditary_nonmatroid')

def source_families():
    star=((0,1),(0,2),(0,3),(0,4),(4,5))
    weights=((4,4),(2,1),(1,2),(2,2),(1,1),(2,1),(1,2))
    return [
        v10_knapsack(),
        Family('source_conflict',6,
               lambda m:all(not(m>>a&1 and m>>b&1) for a,b in star), 'hereditary_nonmatroid'),
        Family('source_two_capacity',7,
               lambda m:all(sum(weights[i][j] for i in bits(m,7))<=c for j,c in enumerate((5,5))), 'hereditary_nonmatroid'),
        Family('source_uniform_matroid',6,lambda m:m.bit_count()<=3,'matroid'),
    ]
