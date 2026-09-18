# C9 endpoint capability compounding checkpoint — 18 September 2026

**Status: bounded prospective capability-compounding evidence. Collatz remains unproved.**

Branch: `collatz-rigid-component-termination-v1`

This checkpoint freezes the first genuinely prospective demonstration of the
endpoint-capability loop:

[
oxed{
	ext{discover endpoint}
	o
	ext{verify exact tail to }1
	o
	ext{compile/cache}
	o
	ext{reuse on future source hits}.
}
]

## Frozen bank before the 27-bit holdout

The bank was frozen before scanning the untouched source interval

[
2^{26}le n<2^{27}.
]

It contained the 10 unique live C9 two-replay endpoints discovered below
(2^{26}):

[
egin{aligned}
&147269353, 153560809, 157755113, 260515561, 373761769,\
&1205282537, 1290217193, 1928799977, 2196186857, 4083623657.
end{aligned}
]

Every bank entry is independently verified by a finite deterministic shortcut
trajectory to (1). Therefore any source that hits a bank endpoint has an
exact lower merge with (1).

## Prospective 27-bit holdout

On the fresh interval

[
2^{26}le n<2^{27}
]

the C9 compounding sweep found **25 live two-replay hits**.

Of these:

[
oxed{15/25}
]

were handled immediately by the frozen bank with zero new endpoint
verification.

The remaining 10 acquisition events collapsed to only **6 unique new
endpoints**:

[
egin{array}{r|r|r}
	ext{endpoint} & 	ext{steps to }1 & 	ext{holdout occurrences}\ hline
733423337 & 166 & 3\
1076307689 & 127 & 3\
2786535145 & 171 & 1\
17417316073 & 164 & 1\
18786756329 & 234 & 1\
64877962985 & 220 & 1
end{array}
]

Every acquired endpoint verified successfully.

Thus

[
oxed{	ext{UNRESOLVED ENDPOINTS}=0.}
]

All 25 live hard hits were closed by either:

1. zero-cost reuse of a previously verified endpoint capability; or
2. one new exact endpoint verification followed by reuse for duplicates.

## Compounding metric

At the source-hit level:

[
rac{15}{25}=60%
]

of the live holdout obligations required no new endpoint proof.

At the novel-obligation level, 10 apparent new source obligations compressed to
6 endpoint capabilities.

This is the first clean prospective evidence in this program that the endpoint
representation produces measurable future proof reuse rather than simply
memorizing source trajectories.

## Promoted bank

The six new endpoint capabilities were promoted only after the holdout
completed. The post-27-bit bank therefore contains 16 verified endpoints.

A fresh 28-bit holdout has been launched with that enlarged bank frozen.

## Scope

This does **not** prove that the endpoint bank is finite, that every future C9
two-replay endpoint reaches a bank member, or that every Collatz trajectory
enters the C9 language.

It establishes only the bounded prospective statement:

> On the untouched 27-bit source band, every live C9 two-replay endpoint was
> exactly certified; previously learned endpoint capabilities transferred
> materially; no unresolved endpoint remained.

The universal residual remains the possibility of endlessly generating
genuinely new, lower-merge-free endpoint/return structure.
