# Finance Review Lab: benchmark specification

Version 0.1 draft. November 5, 2026.

## Purpose

Measure whether AI can audit financial Excel models, correctly repair material errors, and preserve correct work. Publish original evaluations, transparent scores, and inspectable examples on GitHub and Oliver's website. Social posts will communicate findings supported by released results.

This is a proposed evaluation protocol, not a completed benchmark. Four public development workbooks, a conservative grader, offline capture and a local results viewer now exist. There are no measured AI scores, leaderboard, held-out workbooks, or website changes yet. The benchmark name is provisional.

## First-release scope

Twenty scored cases: sixteen error cases and four clean controls, distributed equally across four finance categories. Four additional public development cases support prompt and grader development and never enter headline scores.

| Category | Financial relationships | Scored error cases | Scored clean controls |
| --- | --- | ---: | ---: |
| Operating cash flow | EBITDA to EBIT, tax treatment, capex, change in working capital | 4 | 1 |
| Debt and interest | Debt roll-forward, stated interest convention, principal versus expense | 4 | 1 |
| Enterprise to equity value | Metric/multiple alignment, cash and debt signs, units and diluted shares | 4 | 1 |
| Forecast integrity | Period references, escalation, formula continuity, totals excluding subtotals | 4 | 1 |

The twenty cases are a small initial release. Do not characterize them as representative of all finance work. Exclude full model construction, legal review, security selection, live market data and broad investment judgment from version one.

## What a case contains

Each case has a source/assumptions section, a model, written conventions, an audit task and an isolated reference package. The model has chronological periods, live formulas and consistent banking-style formatting. Workbook complexity follows the financial task; additional tabs must serve a purpose.

Most error cases contain one root cause. Four contain two unrelated root causes. The number of errors is never disclosed in the task. Derived incorrect cells do not count as additional root causes. A repeated bad formula across a schedule is one root cause when one conceptual correction repairs it; unrelated errors remain distinct.

At least two error cases should have misleadingly plausible outputs. Clean cases include legitimate conventions that an overzealous reviewer might try to change. All conventions must be explicit enough to support a defensible reference answer.

The model returns a structured audit memo: finding location, current formula, diagnosis, proposed formula, resulting numerical impact and affected outputs. Version one scores proposed repairs; it does not claim to measure execution of workbook repairs. Actual workbook editing becomes a separately labeled future track.

## Data and originality

Use original synthetic scenarios for the first four development cases. For scored cases, permit synthetic or public-filing-derived inputs, with source type and exact provenance recorded for each case. Do not force public data into a task where it adds no useful realism.

When using real-company data, record filing date, reporting period, exact source page/table, URL, units, retrieved date and every adjustment. Label forecasts as authored assumptions. Reconcile extracted figures to the filing. Do not imply the source company made the planted mistake. The corrupted workbook is an authored evaluation artifact.

Public datasets may inform methodology and provide separate external comparisons. Do not relabel their questions or reference answers as original work. Verify asset-specific reuse terms before redistributing third-party material. A public source is not automatically a redistribution license.

Every case receives: immutable ID, family ID, version, split, source type, scenario, units, explicit conventions, model hash, reference hash, root-cause manifest, expected outputs, numerical tolerances, rubric and validation log.

## Splits and publication

Public development: four cases, including existing case-001. Publish task files, answers and validation so others can understand the benchmark. These are excluded from headline scores.

Private evaluation: twenty cases. Keep workbooks, prompts and reference answers out of the public repository while the test is active. A public case-plan may disclose broad coverage but never the workbook-specific errors or answers. Maintain the private files outside the public checkout; an ignore rule is only a secondary safeguard.

After evaluating, publish all case-level scores and run metadata, plus selected examples with permission/source checks. Any disclosed test case becomes released, not private. Freeze a new version before claiming future evaluations use unseen cases. Never change a flawed case silently: invalidate it across all configurations and reissue results under a new dataset version.

Public leaderboard users can reproduce the public sample evaluation. They cannot independently reproduce hidden-test scores without controlled access; disclose that limitation.

## Scoring

Primary metric: **successful audit rate**, averaged over complete attempts. A case succeeds only when all material root causes are detected, every proposed required repair is valid, required numerical impacts are correct, and no material false correction is proposed. A clean case succeeds when no material false error or required correction is reported.

Numeric correctness alone is not audit success. Correct detection with an incorrect repair fails the primary metric. Hardcoded outputs do not constitute a formula repair. Accept semantically equivalent formulas after checking dependencies and recalculation behavior rather than demanding identical syntax.

Secondary metrics:

| Metric | Rule |
| --- | --- |
| Root-cause recall | Detected reference root causes / all reference root causes in error cases |
| Finding precision | Unique valid root-cause findings / all unique material root-cause findings; no findings = not applicable |
| Valid repair rate | Reference root causes with valid repairs / all reference root causes |
| Clean-case pass rate | Clean attempts with no material false correction / clean attempts |
| Numerical impact accuracy | Required impact outputs within predefined per-case tolerances / required outputs |
| Propagation accuracy | Attempts correctly identifying affected and unaffected downstream outputs / applicable attempts |

Deduplicate findings and group symptoms before precision scoring. A stylistic suggestion is not a false positive unless characterized as a material defect or imposed as a necessary repair. A symptom-only finding may receive propagation credit but not root-cause credit. Unclear finding matches require human adjudication.

Do not combine these metrics into an arbitrary weighted score. Lead with successful audit rate and show error-case and clean-case performance alongside it. Report category counts so a high aggregate cannot conceal aggressive false alarms.

## Grading procedure

1. Preserve the raw answer before parsing. Record malformed output and refusals.
2. Match findings to reference root causes, blinded to model identity where practical.
3. Test proposed formulas in a disposable reference environment, using base inputs and at least two case-specific perturbations. Check intended outputs and untouched logic. Human review assesses explanation and false corrections.
4. Check numerical impacts with predefined absolute tolerances in source units. Set tolerances before model runs, not after seeing answers. Avoid requiring precision unavailable in displayed inputs.
5. Record criterion verdicts, exact supporting answer spans, grader version and adjudication notes. AI judges may assist but are not the sole authority for financial correctness.
6. Human-audit every first-release attempt. Independently recheck disputed and borderline verdicts. Until another human reviewer participates, disclose that grading is single-author rather than independently expert-validated.

The existing development case's primary criteria are detection, repair, magnitude and restraint; propagation is separately reported. This aligns with the new metric. The conservative scoring implementation is now available in frl/grading.py. Human adjudication and unsupported-formula review remain required.

## Evaluation protocol

Freeze case versions, prompts, rubric, tools and stopping rules before scored runs. Begin with two configurations and three repetitions per case: 120 baseline attempts. Add a third configuration only if capacity allows. The repetition count captures variability but does not turn twenty case families into sixty independent cases per configuration.

A configuration includes model/product label, selected reasoning setting if exposed, tool access, workbook inspection ability, execution environment and date. ChatGPT and Codex product configurations are distinct even when their model labels appear similar. Subscription experiments do not establish API-only model rankings. Record unknown settings as unknown.

Give each attempt a fresh context and only the blind package. Prevent filesystem/web access to reference answers. Confirm formula inspection is available using a separate unscored onboarding workbook. Use an identical task prompt and no discretionary hints or performance-driven retries.

Before the pilot, choose and record a per-attempt time/interaction cap and a fixed policy for infrastructure retries. Apply them consistently to scored runs. No cap is fixed in this draft because the pilot must establish practical operation. A model refusal, malformed answer, or failure to finish within the cap counts as an unsuccessful attempt. A confirmed infrastructure failure is recorded separately and rerun under the predefined policy. Never selectively drop failed attempts.

Subscription runs initially use manual transfers or supported independent sessions. Do not assume unattended access, exact tokens, hidden reasoning settings or measurable per-run dollar cost. Record wall-clock duration and visible interaction count. If an API track is added, specify budgets and tool parity separately.

## Reviewer experiment

Secondary experiment on a subset after baseline evaluation works: branch the same initial response into unchanged, self-reviewed and independent-reviewed workflows. Freeze initial answers before review. Keep branches isolated. Record helpful and harmful transitions. An independent-review workflow uses more interactions, so improvement cannot be attributed solely to independence without an additional matched-effort control.

## Release presentation

Website: scope, version/date, score table, case counts, per-category results, protocol, limitations and a few detailed examples. Do not display a ranking until actual verified runs exist. Show uncertainty using case-level resampling with a fixed seed and published method; avoid naive intervals that treat repeated trials as independent cases. With twenty cases, emphasize counts and exploratory findings and avoid superiority claims unsupported by paired evidence.

GitHub: original code, public development cases, schema, scoring tests, run metadata, released examples and reproduction instructions. No credentials, proprietary assets, private cases or personal machine paths in published artifacts.

Social posts: a specific measured finding, denominator, model configuration/date and link to the full report. Distinguish model mistakes, grading uncertainty and dataset defects. Do not manufacture a headline before results.

## Delivery checkpoints

1. **Specification:** this document and the planned case inventory.
2. **Development suite:** four completed public examples; independent calculations, visual QA, input perturbations, style parity and explicit limitations.
3. **Grader:** validated on known correct, missed-error, false-positive, wrong-repair, alternate-formula and malformed submissions.
4. **Pilot:** two configurations on public examples; settle tool parity and stopping rules. No headline capability claims.
5. **Freeze:** author and validate the twenty private cases; freeze versions and hashes before evaluation.
6. **Evaluate:** run the fixed matrix, adjudicate outputs and preserve complete records.
7. **Publish:** GitHub and website release with actual results; publication remains a separate action.

Next build: a debt/interest development case, then a valuation case and a clean operating-model control. Do not mass-produce private cases until the public pilot and grader work.
