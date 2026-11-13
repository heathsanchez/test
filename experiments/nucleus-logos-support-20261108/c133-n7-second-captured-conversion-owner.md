# C133: N7's source argument Expr1477 has a second distinct captured conversion

Status: **WARRANTED_BOUNDED diagnostic**, 2026-11-14 NZDT, isolated C105-lineage
surrogate. No semantic rule/budget change and no standard N7 ACCEPT.

## Native evidence

- Frozen original upstream N7 SHA256
  `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`;
  immutable archive `11272848230`.
- [C133 green native run #43488999538](https://github.com/heathsanchez/test/actions/runs/43488999538),
  [source receipt artifact #14067763626](https://github.com/heathsanchez/test/actions/runs/43488999538/artifacts/14067763626),
  ZIP SHA256 `58ece57adf4e889b095fbd1a08402ed73fae8114931314bf5a726d7624b459f4`.
  Remote isolated revision `e094da6e92f40233dcc8e02b313637c9d51ec461`.
- The source NDJSON confirms `Expr8803 = App(8802,1477)` and
  `Expr1477 = App(1462,624)`. Two experimental relevance/major-demand flags
  unchanged at both budgets. Observer ON/OFF verdict and stdout parity.
  Nine parser tests passed. Historical C124/C125b source not recovered.

## Exact source argument `check_with_formation(Expr1477, domain(Expr8802))`

The type of `Expr1477` is independently **PROVEN** at both budgets in two
captured environments (`application-type-instantiation`, five outer steps).
The conversions, however, are different obligations:

| Captured type/domain pair | Standard 65,536 | Diagnostic 14,155,776 |
| --- | --- | --- |
| actual `Term(Expr110,Env45059,[(Name18,Succ Zero)])` vs expected `Term(Expr1,Env45057,[(Name2,Zero)])` | PROVEN guarded-relational-conversion | PROVEN |
| actual `Term(Expr110,Env66182,[(Name18,Succ Zero)])` vs expected `Term(Expr1,Env66180,[(Name2,Zero)])` | **UNKNOWN unresolved-qualified-recursor-heads** | PROVEN guarded-relational-conversion |

Both have `context=0`, `frame=0`, but the **captured closure** environment IDs
differ. This is a genuine distinction: the source expressions and universe
level substitutions printed identically between calls, but source/capture
identity cannot be asserted from frame IDs or syntax alone. No reuse of the
first conversion is authorized for the second without checking dependent
captures and recursor premises. C131's inference UNKNOWN for outer Expr8804
is downstream of this particular guarded conversion.

## C134 cheapest decisive experiment

At precisely the second conversion owner, read-only capture provenance and
actual used values of `Expr110` and `Expr1`; instrument the first unresolved
registered-recursor pair **only under that owner**. Determine whether a
source-checked stable conversion result or a more efficient checked iota
evaluation can finish within the original budget. Preserve negative controls
and 403-case protected matrix before any semantic promotion. All six valid
original UNKNOWN cases remain open at standard budget.
