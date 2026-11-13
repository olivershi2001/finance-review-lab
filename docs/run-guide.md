# Running a development trial

Python 3.10+ is sufficient for evaluation management, grading and verification. No API key or external service is used by these commands. Run from the repository root.

## 1. Validate assets and export a blind package

```sh
python3 verify_suite.py
python3 -m frl export dev-002 exports/dev-002.zip
```

Exports contain exactly model.xlsx, task.md and sanitized metadata.json. They contain no reference hash, error count, clean flag, rubric or answer key. Export refuses to overwrite an existing ZIP. Choose a new path for a new version. The model file hash is checked against case metadata before export.

## 2. Initialize a run before attempting the case

Copy templates/configuration.json and fill the visible model/product/date/settings, tool access and agreed stopping/retry rules. These settings are operator declarations, not proof that a provider enforced them. Do not use the template's placeholder labels in published results.

```sh
python3 -m frl init trial-001 dev-002 --config configuration.json --mode development
```

The command creates an immutable record and frozen input copies in runs/trial-001/. It freezes the input-package and reference-manifest hashes. Public development cases cannot be initialized in evaluation mode. All actual trials are still pending in the supplied release candidate.

## 3. Run independently

Open a fresh ChatGPT chat or isolated Codex workspace containing only the blind package. Supply its task and prompts/analyst.md. Verify that workbook formula inspection is available. Record the actual duration and interaction count. Do not use this authoring chat or an agent with reference-file access as a blind subject.

Save the answer verbatim to analyst.txt. Extract the requested JSON into analyst.json without rewriting its content. Preserve any extraction limitations in the operator note; the importer hashes raw and structured files separately but cannot prove that a human transcribed them faithfully.

```sh
python3 -m frl import trial-001 analyst --raw analyst.txt --response analyst.json --elapsed-seconds 540 --interactions 1
python3 -m frl grade trial-001 analyst
```

The initial grade is provisional. Supported formulas execute against base and perturbed cell values. Syntax outside the conservative evaluator requires review; a matching numeric result is insufficient for audit success.

For refusal, missing JSON or an incomplete attempt, retain the raw text and specify --status refused, malformed or incomplete. Confirmed infrastructure failures use --status infrastructure_failure and are excluded from scores. Protocol failures count as failed attempts. A completely missing stage remains visible but is not silently treated as an attempt.

## 4. Human adjudication

Copy templates/adjudication.json. For every error, evaluate detection and explanation; evaluate restraint for every case. Supply exact response excerpts and reference-based reasons. Unsupported formula overrides use repair:root-1 with evidence of execution in a disposable workbook and perturbation results. A human override cannot rescue a formula already demonstrated wrong by supported checks.

```sh
python3 -m frl grade trial-001 analyst --adjudication adjudication.json
```

The grader stores immutable grade revisions and retains the previous result. Run metadata and capture records are integrity checks against accidental alteration, not cryptographic attestations of model or human identity. Evidence can still be falsified by a malicious operator; publish raw records and disclose review procedures.

## 5. Optional review branches

Branch the same original answer into self-review and independent review. The self-review branch receives prompts/self-review.md. The separate reviewer gets the blind workbook, task, original answer and prompts/reviewer.md. In a separate branch from the original answer, provide that review with prompts/revision.md. Do not feed self-review into the independent branch.

```sh
python3 -m frl import trial-001 self_review --raw self-review.txt --response self-review.json
python3 -m frl import trial-001 review --raw review.txt
python3 -m frl import trial-001 revision --raw revision.txt --response revision.json
python3 -m frl grade trial-001 self_review
python3 -m frl grade trial-001 revision
```

Each review stage stores the original answer hash. Revision also stores the reviewer hash. The runner enforces record parentage, not whether a provider really isolated contexts. Failed initial captures cannot start review branches. Independent review itself is not a final audit score.

## 6. Export and inspect

```sh
python3 -m frl report reports/my-development-report.json
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/viewer/ and choose the report. Alternatively open viewer/index.html directly and select the JSON file. The explicit simulated example button needs a local server; file selection works without one. Only report files selected by the operator are loaded. The optional example request is local; no external services are contacted.

Filter by evidence type and workflow. Missing optional branches appear as missing records; they are not extra scored failures or planned attempts. Do not compare pooled analyst, self-review and revision rates. Only paired branches from the same original answer support helpful/harmful transition counts.

## Simulated demonstration

```sh
python3 scripts/create-demo.py
```

This constructs fixtures through the real CLI in a temporary workspace and writes reports/demo-report.json. It calls no model and uses scripted adjudication fixtures, not actual human verdicts. The report is labeled simulated throughout. It must never be described as measured performance.
