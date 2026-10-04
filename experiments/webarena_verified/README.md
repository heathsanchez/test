# WebArena-Verified Capability Compiler v1

## Objective

Beat the current public WebArena/WebArena-Verified frontier by treating browser-agent failures as recurring, verifier-defined capability families rather than unrelated tasks.

## Evidence boundary

- Staging repo: `heathsanchez/test`
- Branch: `webarena-verified-capability-compiler-v1`
- Branch base: `4c6274d58a9fca27f24fd6c85508883d1b942cc7`
- Upstream benchmark: `ServiceNow/webarena-verified`
- Upstream benchmark pin: `6473f72db5dcefc97b5725b59e734504edc28a21`
- Development set: official 258-task WebArena-Verified hard subset.
- Evaluator authority: official WebArena-Verified deterministic evaluator.
- No leaderboard claim is WARRANTED until an official-compatible run closes.

## Governing law

The active representation should preserve exactly the distinctions that can change a warranted future:

```
x ~_F y  iff  no protected lawful continuation lets the official evaluator distinguish x and y.
```

For WebArena this means `intent_template_id` is only a syntactic proxy. The stronger unit of reuse is a verifier-relevant obligation/capability family. Static evaluator signatures may nominate such families, but they do not prove behavioral equivalence; only live official-evaluator separators can warrant the merge.

## Current state

INTERESTING -> CANDIDATE.

Static audit of the pinned hard subset found:

- 258 tasks.
- 114 intent templates.
- task types: 74 RETRIEVE, 36 NAVIGATE, 148 MUTATE.
- expected statuses: 248 SUCCESS, 5 NOT_FOUND_ERROR, 5 ACTION_NOT_ALLOWED_ERROR.
- top 20 recurring templates cover 78 / 258 tasks = 30.2%.
- top 40 recurring templates cover 138 / 258 tasks = 53.5%.
- top 50 recurring templates cover 168 / 258 tasks = 65.1%.

A first evaluator-obligation-shape quotient produced 136 CANDIDATE consequence signatures. It is deliberately coarser than concrete expected values and therefore is not a proof of equivalence. It does reveal cross-template reuse opportunities:

- largest candidate family: 11 Reddit mutation tasks spanning 7 intent templates;
- next: 9 Shopping Admin retrieval tasks spanning 6 templates;
- another: 9 Shopping Admin mutation tasks spanning 4 templates;
- another: 8 Shopping retrieval tasks spanning 4 templates;
- another: 8 GitLab/Reddit mutation tasks spanning 2 templates.
- top 5 candidate consequence families cover 45 / 258 = 17.4%.
- top 20 cover 102 / 258 = 39.5%.
- top 40 cover 155 / 258 = 60.1%.

These are candidates for shared capabilities, not warranted equivalence classes.

## Development rule

Encounter -> Verify -> certified residual -> necessary constraint -> least lawful capability change -> Verify -> Compile -> Reclose.

Concretely:

1. Use the official evaluator to define the protected consequence.
2. Cluster tasks only as a CANDIDATE when their evaluator obligations and site/action structure suggest a common capability.
3. Choose the cheapest separator inside that candidate family.
4. Implement the smallest capability that removes the residual.
5. Replay every already-warranted member.
6. Promote a family merge only when all protected continuations tested by the declared boundary remain indistinguishable.
7. Split immediately when a separator exposes a consequential distinction.
8. Compile the passing capability and reclose every other candidate family that can reuse it.

## Cheapest decisive experiment

The first live target remains Shopping Admin template 270 (tasks 108, 110, 111): a three-member RETRIEVE family with no NetworkEventEvaluator requirement and a shared structured month/count response schema.

The experiment is not "hard-code three answers." It is:

- learn one deterministic capability for the underlying order-history aggregation;
- run it from reset state on all three tasks;
- score with the official evaluator;
- require 3/3;
- then test whether that capability requalifies adjacent Shopping Admin retrieval candidate families.

## Promotion rule

- **CANDIDATE**: static family identified.
- **WARRANTED_BOUNDED**: every declared member passes the official evaluator from a reset environment under the stated boundary.
- **REJECTED**: a separator shows the family merge is too coarse or the capability violates benchmark interaction constraints.
- **REUSABLE**: a warranted capability transfers to held-out tasks/templates without special casing.
- **SUPERSEDED**: a later, smaller capability preserves the same protected future at lower prospective cost.

No result from static task definitions alone is a solved-task claim.

The residual mapper is `scripts/webarena_verified_residual_map.py`.


## First live promotion: template 270

**State: WARRANTED_BOUNDED**

A deterministic Shopping Admin capability for monthly counts of completed orders was qualified against the pinned official WebArena-Verified evaluator on hard-set tasks 108, 110, and 111.

Evidence:

- qualification run: `37195574834`
- qualification job: `111416616532`
- branch commit: `5961083a335619fcd71e80664745466473c3921a`
- upstream evaluator/data authority commit: `6473f72db5dcefc97b5725b59e734504edc28a21`
- Shopping Admin image digest: `sha256:d0531dd27ed98d0c459ff9e88118bf2ed8b660b0ed99c38837db46c065a5be13`
- task 108: score 1.0, success
- task 110: score 1.0, success
- task 111: score 1.0, success
- official evaluator version observed: 1.2.3
- evaluator checksum observed in preceding seam run: `35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e`
- data checksum observed in preceding seam run: `d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30`

The capability does not read benchmark expected answers or the container database/filesystem. It derives the requested period from the task, queries the observable Magento Orders Report, filters to completed orders, and extracts the rendered monthly Interval/Orders grid.

### Preserved failed lineage

Two failures remain part of the evidence lineage:

1. Run `37194670382`: the documented env-control `/health` path returned 404 although the application stack was healthy. Readiness was refined to the observable admin surface.
2. Run `37194943969`: the capability produced the exact live counts, but an empty placeholder HAR caused the CLI trace parser to fall through to Playwright JSON-lines parsing.
3. Run `37195408515`: direct evaluator API with `network_trace=None` exposed a Pydantic type mismatch; an empty typed `NetworkTrace` with zero fabricated events is the minimum lawful value for these response-only tasks.

No network-event claim is made for this family because tasks 108/110/111 declare no `NetworkEventEvaluator`.

### Reclosure target

The full 812-task pinned dataset contains two additional template-270 instances not in the hard-set promotion family:

- task 107: May 2022 through December 2022;
- task 109: Jan to December 2022.

These are the next held-out transfer boundary. Passing both without task-specific answers promotes the capability toward REUSABLE; task 109 is also a separator for the date-grammar representation.


## Held-out transfer promotion

**State: REUSABLE within template 270**

After the 3/3 hard-set qualification, the same capability was tested on the two remaining template-270 instances in the full pinned 812-task dataset.

Evidence:

- held-out transfer run: `37195806600`
- held-out transfer job: `111417299539`
- transfer workflow commit: `10de2deffe166a03b8b1d70e7acffe2cfd450736`
- capability grammar refinement commit: `526713444e1fd62de9d9a29a538cd681bb181c98`
- task 107: score 1.0, success
- task 109: score 1.0, success
- same Shopping Admin image digest: `sha256:d0531dd27ed98d0c459ff9e88118bf2ed8b660b0ed99c38837db46c065a5be13`

Task 109 was a useful separator: its period is phrased `from Jan to December 2022`, unlike the explicit-year grammar in the qualification set. The only refinement was to the date grammar; the report-selection, completed-status filter, monthly aggregation, UI extraction, and structured response logic were unchanged.

Thus the declared result is:

```
template 270: 5 / 5 official-evaluator passes
hard-set qualification: 108, 110, 111
held-out transfer: 107, 109
```

This warrants REUSABLE for the template-270 family under the pinned environment/evaluator boundary. It does not warrant a broader Shopping Admin or WebArena leaderboard claim.

## Global reclosure after template 270

The newly compiled primitive exposes an immediate dependency neighborhood: hard-set navigation tasks 707 and 709 use the same Magento Orders Report surface and date-filter semantics but protect a navigation/network consequence rather than a retrieved monthly table. These are the next cheapest separator for whether the compiled report capability can be requalified under a different protected future.


## Cross-template global reclosure

**State: WARRANTED_BOUNDED cross-template reuse**

The compiled Orders Report primitive from template 270 was requalified under a different protected future:

- task 707 / template 268: navigate to last year's sales order report;
- task 709 / template 271: navigate to an explicit-date orders report.

Unlike template 270, these tasks protect both the agent response and the observed network navigation.

Final evidence:

- run: `37196232195`
- job: `111418580676`
- canonical-host refinement commit: `7f01280cabf8b5f8289b3422880596e24bb20c8a`
- artifact: `11301232164`
- artifact digest: `sha256:a5eac01b50e7a41604230131a29de95fb05fbc2c3ec2f6cf6b0f6b032e9150f9`
- task 707: score 1.0, success
- task 709: score 1.0, success
- same Shopping Admin image digest: `sha256:d0531dd27ed98d0c459ff9e88118bf2ed8b660b0ed99c38837db46c065a5be13`

The first cross-template run, `37196053234`, is preserved as a separator. The report type, date range, HTTP method, and response status normalized correctly, but Magento canonicalized the host from `127.0.0.1` to `localhost`. That distinction was irrelevant for response-only tasks but consequential once the NetworkEventEvaluator became protected. The minimal repair was to preserve the canonical host in evaluator configuration. No report semantics or task answers changed.

This is a concrete instance of the governing law:

```
response-only future: 127.0.0.1 ~ localhost
network-protected future: 127.0.0.1 != localhost
=> split exactly at the network boundary
```

Current warranted/reusable closure:

- template 270: 5/5 across hard + held-out full-set instances; REUSABLE within family;
- templates 268 and 271: 2/2 cross-template report-navigation reclosure; WARRANTED_BOUNDED;
- total officially closed tasks in this compiled Orders Report lineage: 7.


## Second compiled family: Shopping Admin payment folds

**State: REUSABLE within template 367**

The second capability uses the observable Magento order grid, preserving its declared default Purchase Date descending order, and compiles:

```
recent-order selection
+ status predicate
+ Grand Total (Purchased)
+ sum / absolute-difference fold
```

Hard-set qualification:

- run: `37226358212`
- job: `111506707784`
- capability live-grid refinement commit: `1f80614ffe84f44d83956d6019bb7019332f1229`
- artifact: `11311624802`
- artifact digest: `sha256:9367052b466ae5534a58e9ef9aa0dad8c24b2c333f66ded54875d4805ef215c7`
- task 193: computed 182.40, score 1.0, success
- task 196: computed 194.25, score 1.0, success
- task 197: computed 778.20, score 1.0, success

Held-out transfer:

- run: `37226580696`
- job: `111507364737`
- pending-predicate generalization commit: `0b8d5057012251208b0df7938f9af4a05603b831`
- transfer workflow commit: `707f1edfbe293f65e74694f46f4f13764abae590`
- artifact: `11311479642`
- artifact digest: `sha256:415861feaf937e32e56007a9716c7d1658b3dde1bd25143e46ccad8098d521df`
- task 194: computed 555.20, score 1.0, success
- task 195: computed 885.40, score 1.0, success
- same Shopping Admin image digest: `sha256:d0531dd27ed98d0c459ff9e88118bf2ed8b660b0ed99c38837db46c065a5be13`

Thus template 367 is 5/5 under the pinned official evaluator and is promoted to REUSABLE within its declared family.

### Preserved payment-fold residual lineage

The failed attempts constrain the representation:

1. `37225462933`: broad pager selector hit Magento UI wrapping and timed out.
2. `37225706722`: native pager activation removed the actionability failure, but no completed rows were collected.
3. `37226023240`: visible-pager refinement still returned zero completed rows.
4. Schema probe `37226224197` exposed the true separator: Magento renders two tables with the same order-grid headers; the first is an empty/template table and the second is the live nonempty grid. The minimal repair was to distinguish visible/nonempty grid from template grid.
5. `37226358212`: after exactly that split, 193/196/197 closed 3/3.

This is another direct instance of consequential refinement:

```
same headers did not imply same protected future
empty template grid != live populated grid
=> E_{t+1} = E_t ∩ ker(nonempty-live-grid)
```

Current compiled Shopping Admin closure now contains:

- Orders Report lineage: 7 official passes (template 270 family plus cross-template 268/271 reclosure);
- Payment-fold lineage: 5 official passes (template 367 hard + held-out);
- total official passes in these two compiled lineages: 12.
