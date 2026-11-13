# Release candidate notes

This is a local development release candidate, not a published benchmark or model leaderboard. No deployment or social post is included.

## v0.2.0 additions

Adds a frozen, randomized manual pilot queue for two configurations, four cases and three repetitions; metadata-blinded human-review packets with enforced artifact bindings; and stricter formula-parser handling of Excel/Python syntax differences. No real campaign, model answer or human verdict has been manufactured.

Native Excel QA now covers eight recalculated/saved workbook copies and 908 formula caches, plus a zero-rate input change. Print spacing in the three newer cases was tightened after preview found an orphaned check; their six sheets were then inspected in whole-workbook A4 landscape preview. Font sizes and financial logic are unchanged. Case versions are now 0.2.0; do not compare new hashes with old frozen attempts. Native evidence source hashes are checked by the release tests.

## Results explorer

Open `viewer/index.html` directly in a modern browser. Choose a JSON report produced by the run-management exporter. The viewer has no external libraries or embedded results. The optional Load simulated example button requests only the local project report; it contacts no external service. If opening with file:// blocks the request, select reports/demo-report.json with the file picker. It reads local files in the browser and uses text-only insertion for response content.

Reports use schema version `1.0`. Runs contain configuration metadata, evidence mode (`simulated`, `development`, or `evaluation`), case and split metadata, and stage records. Attempt grades are read from `stages.<stage>.grading.grade`. The independent review itself is displayed as evidence and is not scored as an analyst answer.

Integrity-verified human-adjudicated attempts and unequivocal protocol failures enter score denominators. Malformed, refused, incomplete and timed-out responses count as failures; missing answers, infrastructure failures, pending grades and unverified records remain visible but are excluded. Evaluation-mode rows must use private, private_eval or released_eval splits. Mixed evidence modes or workflows do not produce pooled capability rates. Configuration tables separate workflow stages. Helpful and harmful revisions require finalized initial and final answers plus matching parent hashes; independent revisions also require matching, verified review evidence.

No results are shown by default. Simulated fixtures must be labeled as such. A lack of actual blind evaluation results is not a zero-percent performance finding.

## Interpretation boundaries

Public development examples support methodology and software validation. They do not establish unseen-case performance. A configured product comparison does not isolate underlying model intelligence, and independent review uses more interactions than the baseline. Small case sets support exploratory findings, not sweeping superiority claims.

The grader evaluates proposed repairs within explicitly supported financial and formula checks. It is not an unrestricted Excel engine. Human adjudication remains necessary. Native Microsoft Excel recalculation and printed-page rendering require separate verification and must not be inferred from other tooling.

For current case and test completion evidence, consult the generated validation reports and project progress log. This note does not certify checks that have not been run.
