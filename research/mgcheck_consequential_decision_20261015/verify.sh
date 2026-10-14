#!/usr/bin/env bash
set -euo pipefail
E="research/mgcheck_consequential_decision_20261015/evidence"
mkdir -p "$E/gimmes-review" "$E/gimmes-native" "$E/runs"

# Only API GET requests for previously public frozen GitHub Actions artifacts
# and source, no third-party repository writes or production App changes.
gh api /repos/heathsanchez/test/actions/artifacts/11929970762/zip > "$E/gimmes-review.zip"
gh api /repos/heathsanchez/test/actions/artifacts/11929207814/zip > "$E/gimmes-native.zip"
printf '%s  %s\n' \
 "590e19d88f3203b7915084eab71615d27bf8aca373d254cf666abdc5a28e7df4" "$E/gimmes-review.zip" \
 "0e567242796ff0a68fadb4ded8fe754b0721c450b221d5733b9edad1be793fbe" "$E/gimmes-native.zip" | sha256sum -c
unzip -q "$E/gimmes-review.zip" -d "$E/gimmes-review"
unzip -q "$E/gimmes-native.zip" -d "$E/gimmes-native"

curl --fail --silent --show-error --location \
 "https://raw.githubusercontent.com/heathsanchez/test/20864090c084efc0511cffcf47aae556b4003fea/research/mathgraph_pr958_one_finding_20261015/ONE_FINDING_REPORT.json" \
 -o "$E/yaml-source-report.json"

for run in 38559572638 38560167831 38560825707 38638946524 38639617928; do
  gh api "/repos/heathsanchez/test/actions/runs/$run" > "$E/runs/$run.json"
done

node --test research/mgcheck_consequential_decision_20261015/decision-closure.test.mjs
