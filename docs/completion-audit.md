# Release candidate completion audit

Audit scope: the autonomous build instructions for a local development release candidate. Publishing, paid services and real hidden-test scores are outside this build. This record reports completed artifacts and explicit verification limits, not future benchmark performance.

| Requirement | Current evidence | Result |
| --- | --- | --- |
| Four original public development cases | cases/ and references/ each contain case-001, dev-002, dev-003, dev-004 | Complete |
| Brief, input workbook, reference, manifest, expected values, rubric, validation for each | Files present; actual-manifest and export tests inspect them | Complete |
| Correct financial relationships | 150 independently recomputed forecast outputs across four reference cases; base probes match XLSX caches | Passed |
| Live input changes and boundaries | Authoring-engine tests for working-capital assumptions, zero interest, repayment changes, zero cash/shares, capex changes and negative EBIT | Passed within tested conventions |
| Exact planted changes and clean control | Exported XML comparison finds I39, G20, G21 respectively; no changes in clean case; expected downstream cache changes only | Passed |
| Formatting and layout | Nine sheet previews visually inspected; identical input/style checks; panes/gridlines/print metadata verified | Passed in available tooling |
| Native Excel recalculation and page rendering | Eight disposable workbook baselines / 908 formula caches; one zero-rate input test; six sheets in native print preview | Passed in recorded scope; original case print layout and physical printing unverified |
| Grader and adversarial submissions | Equivalents, probes, hardcodes, invalid numerics, conflicting duplicates, false positives, symptoms, clean controls, malformed/refused responses | Tested |
| Unsupported repairs and human evidence | Unsupported formulas route to review; human detection/explanation/restraint gates; successful_audit null until finalized | Tested |
| Subscription run workflow | Blind ZIP allowlist, config, immutable raw/structured captures, hashes, branches, grade revisions, failed statuses and report integration | Tested |
| Denominators | Failed attempted tasks count as failures with reference denominators; infrastructure/missing/pending visible and separate | Tested |
| Viewer | Local browser empty state, simulated load, analyst filter, denominators, safe text rendering tests, review-pair logic and sticky evidence label | Passed at available panel width |
| Demonstration report | Four constructed simulated runs generated via real CLI; no model calls or real human verdicts | Complete, explicitly simulated |
| Actual blind pilot | No genuinely restricted evaluation session established; shared authoring context has answer access | Not run; manual packages prepared as permitted |
| Source release and docs | README, protocol, run guide, authoring instructions, provenance, licenses, tests, CI definition, website/social drafts | Complete |
| Private-case infrastructure | External empty-workspace utility plus isolation checklist and safety tests | Complete; no hidden tasks generated |
| Publication | No GitHub push, deployment or social posting | Not performed as requested |

## Commands and coverage

Current v0.2.0 test counts and fresh-archive checks are recorded in release-verification-v0.2.0.json beside the archive. Coverage includes independent saved-workbook verification, blind-package checks, frozen campaigns, bound human review packets and native evidence hashes. Viewer DOM tests use synthetic inputs. GitHub CI is configured but has not run remotely.

`python3 verify_suite.py`: four cases passed; original case has 50 independent forecast values, additional cases have 100. Further assertions verify planted impacts, propagation, reconciliation, style/input parity, hashes, formula changes and absence of cached Excel errors/cycles. A finite check is not a claim of universal correctness.

The source archive uses an explicit allowlist and a SHA-256 file manifest. A fresh-copy reproduction check is recorded separately in release-verification.json beside the archive after packaging. That check proves the shipped Python and viewer software tests can run without local authoring dependencies. Optional workbook regeneration still requires separate Artifact Tool access.

## Remaining substantive work

Human financial review and blind development trials remain required before publishing model findings. Additional native input boundaries and original-case print review remain open. The planned twenty private cases, measured model leaderboard and hosted website are future phases. No outputs in this release should be described as completed evidence of those phases.
