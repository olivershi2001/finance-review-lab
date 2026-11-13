# Build progress

November 12, 2026. Source published to GitHub; initial hosted checks passed. One real development smoke trial is captured locally and awaits human scoring. The November 6 native Excel evidence is retained with its original scope.

| Milestone | State | Evidence |
| --- | --- | --- |
| Four public cases | Built | cases/ and references/ contain eight XLSX files, briefs, manifests, outputs and rubrics |
| Excel QA | Passed in authoring engine and independent checks | Input perturbations, exact formula/style comparisons, cycle/error scans, Decimal recomputation; all nine sheets visually inspected |
| Native Excel | Tested within recorded scope | Eight workbook baselines / 908 formula caches, one zero-rate input change; six sheets in whole-workbook print preview |
| Grader | Implemented | Restricted formula execution, three probes per error, numeric checks, human review gates and controlled-submission tests |
| Offline run workflow | Implemented | Blind export, immutable capture, frozen hashes, review parentage, grade history, failure states and report tests |
| Pilot campaign | Implemented, not run | Balanced reproducible 24-trial planner, frozen configurations/prompts/packages, explicit planned/initialized/captured states |
| Human review packets | Implemented, awaiting people | Metadata-blinded HTML and null decision worksheets; exact response/manifest binding enforced at import and report reproduction |
| Results explorer | Implemented | Browser checked at a narrow desktop panel width; explicit simulated demo, filters, workflow separation, traces and evidence |
| Development smoke trial | Captured, provisional | Fresh ephemeral Codex session with restricted command access; reference-read canary blocked; human review pending; not a comparative campaign |
| GitHub publication | Public | See github-publication.md for repository and initial hosted CI evidence |
| Release documentation | Prepared | Run guide, provenance, authoring instructions, methodology, source archive utility and unpublished writing drafts |
| Private evaluation | Infrastructure only | Empty-workspace utility and isolation checklist; no hidden tasks authored or scored |

## Verification record

The original case's reference outputs were separately recomputed by an AI review agent. The three additional cases are checked with independently written Decimal calculations. The saved XLSX suite is checked against intended root changes and downstream effects. Check files record their precise coverage. This is authoring QA, not human financial validation.

The original three sheets and six new sheets were visually inspected. New workbooks have chronological periods, blue inputs, green cross-sheet links, black same-sheet formulas, frozen headers/labels and landscape print metadata. No comments or external workbook links are used. The correct and audit versions have identical input values and styles.

The results viewer was opened in the local in-app browser, including its empty state and explicitly simulated example. The sample demonstrates helpful and harmful revisions, a clean pass and a malformed failure. No actual model or human adjudicator produced these fixtures.

Final command counts and release archive validation are recorded in completion-audit.md after the release checks finish. Unit/DOM fixtures are software evidence, not model results.

## Next substantive task

Have a separate human review the development cases and first captured answer, then run the comparative development campaign. The preliminary command-access checks do not independently certify every model-session surface. The first real smoke test exposed a downstream-address normalization defect, now fixed in grader 0.2.1 with regression tests; both grading revisions and the original model response are preserved locally. Freeze stopping rules and tool parity before the comparative pilot. Then author the private evaluation set in an access-isolated workflow and run measured evaluations. Do not claim these public examples are unseen or create a real leaderboard from simulated records.
