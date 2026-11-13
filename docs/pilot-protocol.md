# Pilot protocol

## Status

Four public synthetic development cases have been built. One real, access-restricted development smoke trial was captured on November 12, 2026; it remains provisional pending human review. The comparative pilot has not run. See development-smoke-trial.md for scope and limits. The offline runner and grader are documented in run-guide.md. The legacy numerical scaffold is excluded from this release.

## Data provenance and finance conventions

Original synthetic historical data and assumptions were chosen for a fictional industrial distributor. No employer information, market data, proprietary skills, or Mercor dataset is used. Actuals are synthetic reported amounts. Forecast D&A and capex use explicit revenue ratios; the simplified model does not claim to be a full three-statement model. Historical effective tax rates are calculated from the synthetic reported amounts and can differ slightly from forecast rates.

Arial 10-point body, 14-point titles. Calendar years align across tabs. Numerical inputs are blue, same-sheet formulas black, cross-sheet formulas green; check results are neutral with conditional warnings. Forecast editable inputs use pale amber. Negative amounts use parentheses, zero monetary amounts use dashes, rates have one decimal, and reconciliation differences show two decimals. Underlying precision is retained. Gridlines are hidden; headings and identifying columns are frozen. Print areas use landscape pages fitted to one page wide. Neither file contains external workbook links. Both files have identical styles, layout and explanatory text.

## Blind execution

1. Copy only `cases/case-001/` into a fresh isolated folder or upload its two files to a fresh chat. Evaluation sessions must not access `references/`, the builder, or this protocol.
2. Record model label, date, tool access, reasoning setting if visible, and whether the model could inspect formulas. Do not treat a screenshot-only attempt as equivalent to workbook access.
3. Save the analyst's initial response verbatim as A.
4. For B, branch from A and ask: “Recheck your audit independently against the supplied workbook and conventions. Verify calculations, remove unsupported findings, and return your final audit memo and JSON.” Save the final response.
5. For C, use a fresh reviewer chat with the blind package and A. Ask it to audit the proposed answer, verify each finding and return recommended corrections. It must not see B or the answer key.
6. In another branch from A, provide the review and ask the analyst to verify it and submit its final memo and JSON. Save both review and final revision.
7. Adjudicate A, B and C against the reference rubric. Record helpful and harmful transitions from the same A. Preserve failures and missing runs.

Without branch support, recreate context with the exact original messages and initial answer, and disclose that replay. Do not silently compare runs with different tool access. A human operator transfers responses in this subscription-based pilot. No unattended subscription automation is assumed.

## Interpretation

This first case is a development fixture. Its authoring chat has seen the answer, so it cannot produce a blind performance result on the case. One case cannot estimate reviewer effectiveness. C uses more interactions than B, so any benefit cannot be attributed solely to independence. No API costs or exact token use are asserted for subscription runs. Once the four-case development pilot works, freeze the protocol and add unseen, structurally different cases before measuring capability.
