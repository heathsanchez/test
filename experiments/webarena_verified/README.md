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


## Third compiled family: visible order selectors

**State: REUSABLE within the supported visible-grid subfamily of template 366**

The third capability reuses the observable Magento order grid and compiles:

```
global recency normalization
+ status predicate
+ visible attribute projection
```

Qualification/transfer evidence:

- final run: `37232747941`
- final job: `111525717689`
- evaluator-key refinement commit: `eb1fa5daf85048a29abf1de0d82cf8c3fed38290`
- artifact: `11314258912`
- artifact digest: `sha256:83a55e1729280c778f663c9c9bef79108d75eb137511f779b1bbcde5de438100`
- hard task 200: score 1.0, success
- held-out 199: score 1.0, success
- held-out 202: score 1.0, success
- held-out 203: score 1.0, success

The failed lineage is preserved:

1. `37227052863`: task 203 selected the correct most-recent pending order and correct date/order ID values, but emitted the field name `purchase_date`.
2. The official task schema protects the object key `date`, so the evaluator rejected the otherwise correct value.
3. The minimal repair changed only that consequential representation key. No order-selection logic, date value, or status logic changed.
4. `37232747941`: 200/199/202/203 all closed.

This establishes REUSABLE only for the currently supported visible-grid projection boundary. Template-366 tasks requiring hidden/detail-page fields (customer email, order items) remain outside this promotion.

Current compiled official-pass ledger:

- Orders Report lineage: 7 total passes, 5 hard-set.
- Payment-fold lineage: 5 total passes, 3 hard-set.
- Visible-order-selector lineage: 4 total passes, 1 hard-set.
- total across compiled lineages: 16 official passes, of which 9 are hard-set tasks.


## Fourth compiled family: customer order counts

**State: REUSABLE within template 276**

This capability reuses the Magento order grid, exposes the existing hidden Customer Email column through the UI, scans the complete order history, groups by customer email, and applies exact-count or completed-order rank predicates.

Evidence:

- final run: `37233155555`
- final job: `111526909967`
- numeric-checkbox residual repair commit: `988253088112646fb93f0a6383293523bb0ea073`
- artifact: `11314209306`
- artifact digest: `sha256:534a26d157b4829191777766898f45059cc524704b61900c591fe4d5fd42add9`
- hard 63: score 1.0, success
- hard 64: score 1.0, success
- hard 65: score 1.0, success
- held-out 62: score 1.0, success
- each live execution scanned 308 order rows and 36 unique customer emails.

Preserved separator:

- first run `37232981554` failed before evaluation because Magento generated the Customer Email checkbox with numeric DOM id `14`; CSS selector `#14` is invalid.
- the minimal repair selected the checkbox relative to its label instead. No counting, ranking, or customer semantics changed.

Current compiled official-pass ledger:

- Orders Report lineage: 7 total / 5 hard.
- Payment-fold lineage: 5 total / 3 hard.
- Visible-order-selector lineage: 4 total / 1 hard.
- Customer-order-count lineage: 4 total / 3 hard.
- cumulative: **20 official passes total / 12 hard-set tasks**.


## Fifth compiled family: search-term analytics

**State: REUSABLE across templates 285 and 1001 under the declared response-only boundary**

The capability reads the observable Magento Search Terms grid and compiles:

```
Search Query + Results + Uses
-> rank by Uses
-> optional Results > 0 availability guard
```

Evidence:

- final run: `37234527817`
- final job: `111530890573`
- stable legacy-pager refinement commit: `072db26b1ca56d3eb672286099733246184053a5`
- artifact: `11314957646`
- artifact digest: `sha256:6d5da750fc5cb870bcb68e15a622da12b8496014ebea1b1ecdfaae026e143b78`
- hard 42: score 1.0, success
- hard 127: score 1.0, success
- held-out 41: score 1.0, success
- held-out 43: score 1.0, success
- each execution scanned 7 live search-term rows.

Preserved separator:

- first run `37234278585` failed before evaluation because the legacy grid's Next button did not provide the same stable row-change contract as the modern UI grids.
- the minimal repair used Magento's own stable legacy pager controls: page size 200 and explicit current-page input. Ranking semantics were unchanged.

Current compiled official-pass ledger:

- Orders Report lineage: 7 total / 5 hard.
- Payment-fold lineage: 5 total / 3 hard.
- Visible-order-selector lineage: 4 total / 1 hard.
- Customer-order-count lineage: 4 total / 3 hard.
- Search-term analytics lineage: 4 total / 2 hard.
- cumulative: **24 official passes total / 14 hard-set tasks**.


## Sixth compiled family: selected-order detail transport

**State: WARRANTED_BOUNDED cross-state reuse; held-out transfer passed**

The existing order-grid selector was transported into Magento's selected-order detail page.

Evidence:

- run: `37242072336`
- job: `111552629194`
- workflow commit: `7ad6fdcf79bba882abf080c5c391514859c9d1d9`
- artifact: `11317936723`
- artifact digest: `sha256:23c23f079e4408177a3dd117f150a902c121d6b4a568f4ffe1398ea6d9d6259b`
- hard 204: score 1.0, success
- held-out 198: score 1.0, success

This reuses the already-compiled recency/status selector, then follows the selected order's own View link. Hard task 204 extracts product names and final prices from the Items Ordered table and preserves the requested low-to-high price ordering. Held-out 198 extracts the customer email from the Order & Account Information table.

The capability therefore demonstrates transport of the same selected-order identity across two representations:

```
order-grid row
-> certified selected order
-> order detail page
-> protected detail projection
```

The compiled hard reclosure has been expanded from 14 to 15 tasks and must pass before 15 is treated as the new replayed score floor.


## Compiled hard reclosure v2

**State: WARRANTED_BOUNDED — 15/15**

The compiled hard closure was replayed after adding selected-order detail transport.

Evidence:

- run: `37242286450`
- job: `111553237827`
- workflow commit: `535c4dc3d9c23b7d15a13db8f695005028e31b6f`
- artifact: `11318155246`
- artifact digest: `sha256:c177893cb413a8231e80923b5d3f87ca1ca33ddeb6483ee905674307c7d3dbdf`
- official scores: all 15 tasks = 1.0, success
- task IDs: 108, 110, 111, 707, 709, 193, 196, 197, 200, 63, 64, 65, 42, 127, 204.

This supersedes the prior 14-task replay seal as the current compiled hard score floor.


## Compiled hard reclosure v3

**State: WARRANTED_BOUNDED — 17/17**

The compiled hard closure was replayed after adding exact-product review-rating retrieval.

Evidence:

- run: `37243635510`
- job: `111557120117`
- workflow commit: `ce878fb44c51b6359147d5e47175fab09fb4ed7b`
- artifact: `11318062892`
- artifact digest: `sha256:11606caf236a0c613740f31646457833da659fb5b37686915f77cbad5ecb06ed`
- all 17 official scores = 1.0, success
- task IDs: 108, 110, 111, 707, 709, 193, 196, 197, 200, 63, 64, 65, 42, 127, 204, 113, 214.

This supersedes the 15-task seal as the current replayed hard score floor.

The review-rating family is WARRANTED_BOUNDED on hard tasks 113 and 214. Its held-out transfer is not yet REUSABLE: task 115 exposed an over-merge between `Chloe tank` and the related product `Chloe Compete Tank`. That separator is preserved; no broader product-identity claim is made.


## Compiled hard reclosure v4

**State: WARRANTED_BOUNDED — 21/21**

The current compiled Shopping Admin hard closure replayed successfully in one reset environment under the pinned official evaluator.

Evidence:

- run: `37244204875`
- job: `111558740280`
- artifact: `11319035648`
- artifact digest: `sha256:7fc8bfe76d07c3907d5815fd0e21c775b94367d57f2e9f316ba42374eba9bd43`
- all 21 official scores = 1.0, success.

This supersedes the 19-task seal as the current replayed hard score floor.

## Customer phone lookup

**State: REUSABLE — 5/5 within template 364**

- hard 212: score 1.0
- held-outs 208, 209, 210, 211: all score 1.0
- run: `37244285228`
- job: `111558972798`
- artifact: `11318786930`
- artifact digest: `sha256:15d05a91b6f5c9208bc0246fea406c0f3af401d5b66d93ea000141d8fa9b27c6`

The held-out separator was phone-number representation: a leading US country code `+1` must be normalized against Magento's stored ten-digit national form. The customer identity/name/email lookup logic was unchanged.

## Review count closure

**State: REUSABLE — 10/10 across templates 288 and 248**

Term-count tasks use Magento's server-side Review-detail filter; date/count tasks use the server-side Created-date filter and grid total. The earlier representation that scanned truncated Review cells was rejected.

Evidence:

- run: `37244403567`
- job: `111559312176`
- artifact: `11318896715`
- artifact digest: `sha256:a7f1306ff6bade465996fe41ef63f12ab0e1991fd9f2d018ed84edae65c1f74a`
- hard 11: score 1.0
- hard 15: score 1.0
- hard 345: score 1.0
- held-outs 12, 13, 14, 344, 346, 347, 348: all score 1.0

The key separator was consequential information loss: the visible grid truncates review detail text, so term matching must use the server-side full-detail filter rather than the rendered truncated cell.


## Compiled hard reclosure v5

**State: WARRANTED_BOUNDED — 22/22**

The compiled hard closure was replayed after adding the review date-count capability.

Evidence:

- run: `37244596332`
- job: `111559864357`
- workflow commit: `d6d83884aff855dcb180feaa0156c768183bb791`
- artifact: `11318791615`
- artifact digest: `sha256:51f6f741b4a8ba4187c6b52324766e424bdffe931ad0b0030dcdc8ad7ec07866`
- all 22 official scores = 1.0, success.
- task IDs: 108, 110, 111, 707, 709, 193, 196, 197, 200, 63, 64, 65, 42, 127, 204, 113, 214, 212, 184, 11, 15, 345.

This supersedes the 21-task seal as the authoritative replayed hard score floor.


## Reddit Books top-ten family

**State: REUSABLE — 4/4 within template 17**

One live `/f/books/hot` snapshot is reduced to the top ten submissions, then each candidate is re-opened through its internal Postmill permalink so classification is based on submission content rather than external title links or comment text.

Evidence:

- run: `37245823093`
- job: `111563402323`
- artifact: `11319291215`
- artifact digest: `sha256:efdb248a87303932a381758f23d8788a3c2f430383eb0f04bcc5a7d70d13fe71`
- hard 66: score 1.0
- hard 67: score 1.0
- hard 68: score 1.0
- held-out 69: score 1.0

The preserved separator was title-link identity: a hot-list title may point to an external article, while the protected post state lives at the internal Postmill permalink. The capability therefore transports the selected hot-list post into its internal submission representation before extracting protected consequence.

## Reddit newest-post comment family

**State: REUSABLE — 5/5 within template 33**

The capability resolves the requested forum from the live forum index/search surface, opens its New view, selects the first submission, follows the internal permalink, and counts comments whose observed net score is negative and whose author differs from the submission author.

Evidence:

- run: `37246088405`
- job: `111564176891`
- artifact: `11318743343`
- artifact digest: `sha256:6b9ddd1d118adfe79bc57a11f2f5cadbc26c2a0009f0af0a7b27cb6dd60f06de`
- hard 28: score 1.0
- hard 29: score 1.0
- hard 31: score 1.0
- held-out 27: score 1.0
- held-out 30: score 1.0

This raises the individually warranted hard-task set to **28**. The cross-site 28-task replay remains the authoritative promotion gate before 28 is called the replayed score floor.


## Compiled cross-site hard reclosure v1

**State: WARRANTED_BOUNDED — 25/25**

The compiled closure now spans two independently reset benchmark sites: Shopping Admin and Reddit.

Evidence:

- run: `37246143552`
- job: `111564334037`
- workflow commit: `e2ac19e4dd87821e8c8ddd8919eea05661b8ae5d`
- artifact: `11319133733`
- artifact digest: `sha256:1693fbfb34b8911ae5a638515c43e11f084ff7c458e9c7f4bc85ba3f175d9e38`
- all 25 official scores = 1.0, success
- boundary: 22 previously compiled Shopping Admin hard tasks + Reddit hard 66, 67, 68.

This supersedes the 22-task single-site seal as the authoritative replayed hard score floor.

## Rejected notification-precondition hypothesis

Task 491 does **not** fail because the named customer lacks a pending order.

Run `37246303426` reused the verified Magento order-grid scanner and found:

- customer: Sarah Miller
- pending order: `000000299`
- purchase date: May 31, 2023 2:55:09 AM

Therefore:

```
no pending order => ACTION_NOT_ALLOWED
```

is REJECTED as the explanatory rule for task 491. The next separator must be inside the selected order's notification/comment action or another task-specific admissibility condition. No task-491 pass is claimed.


## Compiled cross-site hard reclosure v2

**State: WARRANTED_BOUNDED — 28/28**

The compiled closure now replays 28 hard tasks across independently reset Shopping Admin and Reddit environments.

Evidence:

- run: `37246366927`
- job: `111564966237`
- workflow commit: `7ac98de22e01a59ca6a852079c58172de19c171a`
- artifact: `11318724028`
- artifact digest: `sha256:ec7fc37d461fb1d2413b29a65f1c2088f58d91f967085bbf2ed33ff14d833c76`
- all 28 official scores = 1.0, success
- Reddit additions beyond the prior 25-task seal: hard 28, 29, 31.

This supersedes the 25-task cross-site seal as the authoritative replayed hard score floor.


## Shopping low-star review-title family

**State: REUSABLE — 5/5 within template 136**

The public product page is not a static sufficient representation: Magento reports the review count immediately, but review rows are lazy-loaded only after activating the Reviews tab. The minimum repair was to activate that tab, wait for live review rows, then project review title + rating and follow review pagination.

Evidence:

- run: `37246995788`
- job: `111566723227`
- artifact: `11319301914`
- artifact digest: `sha256:1036a246b13adff4a5c9e49d3c111bbb3bf04ff8a46ff2d0cc3570374c98f49c`
- hard 163, 165, 166: all score 1.0
- held-outs 164, 167: all score 1.0

The branch was reverted to the exact known-green implementation in commit `6314057bd6dedd0d136101894741b7b7aaec783a`; a later unneeded activation-path refinement was not retained.

## GitLab personal-project star family

**State: REUSABLE — 5/5 within template 289**

The capability logs into the pinned GitLab environment as the benchmark's seeded user, enumerates the complete personal-project listing with observed star counts, opens each project to recover its visible project ID, then applies the requested star predicate.

Evidence:

- run: `37246547955`
- job: `111565473919`
- artifact: `11319258386`
- artifact digest: `sha256:c42845f7ecc69551c909230c4a9072c01e0be2aca95939fcb1d30ca0e49a5962`
- hard 170, 171, 172: all score 1.0
- held-outs 168, 169: all score 1.0

Observed personal-project state included 12 projects spanning star counts 0, 1, 2, and 6. The same live representation therefore supports least-star, less-than-five, zero-star, most-star, and >100-star predicates without task-specific project IDs.

The individually warranted hard-task set is now **34**. A four-site 34-task reclosure is the promotion gate before 34 becomes the replayed score floor.


## Compiled cross-site hard reclosure v4

**State: WARRANTED_BOUNDED — 34/34 across four sites**

The compiled closure now replays 34 hard tasks across independently reset Shopping Admin, Reddit, Shopping, and GitLab environments.

Evidence:

- run: `37247557913`
- job: `111568344723`
- workflow commit: `1e692e5515f5aac80ca139dfccb0c222cba04ab7`
- artifact: `11319961405`
- artifact digest: `sha256:a9b7fac6729cff449d0f8eff9793bfea2d4be009db79e7d6780a99ded8be313e`
- all 34 official scores = 1.0, success
- boundary: reset Shopping Admin + Reddit + Shopping + GitLab environments under pinned upstream authority `6473f72db5dcefc97b5725b59e734504edc28a21`.

Task IDs:
`108, 110, 111, 707, 709, 193, 196, 197, 200, 63, 64, 65, 42, 127, 204, 113, 214, 212, 184, 11, 15, 345, 66, 67, 68, 28, 29, 31, 163, 165, 166, 170, 171, 172`.

This supersedes all earlier single-site and cross-site seals as the authoritative replayed hard score floor.


## GitLab author/date commit-count family

**State: WARRANTED_BOUNDED — 3/3 hard**

The capability transports the current repository identity into GitLab's authenticated repository-commits API and counts commits inside the protected author/date interval. This replaced the rejected assumption that the rendered commits page supports ordinary `?page=N` pagination.

Evidence:

- run: `37254286983`
- job: `111587975035`
- artifact: `11321984263`
- artifact digest: `sha256:fdb08c2122e8471bd2e4bd3e2b846e813898da47e0b621fb2ee582ab2c19c279`
- hard 303: count 1, score 1.0
- hard 304: count 14, score 1.0
- hard 307: count 5, score 1.0

Preserved separator: the first implementation reread the same 40 rendered commits when adding `?page=2`. Exact authenticated API pagination plus prefix-compatible author identity (e.g. `Kilian` -> `Kilian Valkhof`) is the minimum sufficient representation.

## GitLab project-member family

**State: WARRANTED_BOUNDED — 2/2 hard**

The capability resolves the requested project, opens GitLab's rendered `/-/project_members` page, and reads usernames from stable `members-table-row-*` records while excluding the benchmark user.

Evidence:

- run: `37254281067`
- job: `111587956565`
- artifact: `11322004243`
- artifact digest: `sha256:ee5dde982e7570e01b857be6d5b74710796d117ffffcaecf5f9595eb2d1525c2`
- hard 349: `yjlou`, score 1.0
- hard 350: `abisubramanya27`, score 1.0

The individually warranted hard-task set is now **39**. The 39-task cross-site reclosure is the promotion gate before 39 becomes the authoritative replayed floor.
