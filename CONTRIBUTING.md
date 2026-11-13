# Contributing

Finance Review Lab is a development benchmark toolkit. Contributions should improve task quality, reproducibility, grading or review evidence. Public examples are not hidden tests and simulated records are not model scores.

## Run the checks

```sh
python3 -m unittest discover -s tests -v
python3 verify_suite.py
node --check viewer/app.js
node viewer/test-viewer.cjs
```

Python 3.10+ is sufficient for the offline workflow; it has no third-party Python dependencies. Node 18+ is needed only for viewer tests. Workbook regeneration uses a separate authoring runtime; see docs/case-authoring.md before changing a workbook.

## Useful first contributions

- Review a public case's stated finance conventions and reference calculations; identify exact cells and explain any defect.
- Test a proposed equivalent repair in native Excel and document its behavior under changed assumptions.
- Run a blind development attempt in a fresh session using only an exported package. Retain the original answer, settings, elapsed time and all failed attempts.
- Perform human review using docs/human-review.md. Leave unknown or unfinished judgments pending.

Reference defects need versioned corrections. Preserve earlier evidence and explain which task versions are affected; do not silently rewrite reference answers or scores. Changing source workbook bytes invalidates recorded native evidence until it is renewed.

## Data and evidence

Use original synthetic material or public sources with recorded provenance and compatible redistribution terms. Do not contribute employer models, proprietary prompts, paid-platform tasks, credentials, personal contact data or private evaluation cases to this public repository.

Keep local runs, campaigns, model configurations and human-review worksheets outside commits. Reports intended for publication need a separate content review. The supplied demo remains explicitly simulated. A self-attested review record does not by itself establish independent expert validation.

Code contributions use MIT; original case/reference contributions use CC BY 4.0, matching the repository's licenses. Make a pull request with the problem, concrete change, checks run and any remaining limitations.
