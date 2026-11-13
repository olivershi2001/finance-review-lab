# First real development smoke trial

On November 12, 2026, one real public-development attempt was captured locally using Codex CLI with ChatGPT sign-in. The requested configuration was `gpt-6.1-sol`, high reasoning, with a strict final JSON schema, one initial instruction, a 600-second cap and no infrastructure retries. It used the public debt/interest development case. This was a workflow smoke test, separate from the planned 24-trial comparative pilot.

## Observed execution

The candidate started in a fresh ephemeral session and a separate temporary folder containing only the exported workbook, task and sanitized metadata. User config and project guidance were excluded; memory injection, apps/plugins, browser use, delegation and command networking were configured off. Authentication was restricted to ChatGPT sign-in and API-key variables were removed from the child environment. Existing global user settings and credentials were not changed.

A preflight using the same command permission profile confirmed that the workbook was readable, the reference manifest was blocked, and Python could inspect the XLSX archive. The actual trace contains four completed local commands, which read the blind brief/workbook and calculate from those inputs. The final answer was captured in approximately 58.46 seconds with no additional instruction or retry.

This is an observed local setup, not an independently certified isolation system. The preflight checks command file access; it does not prove every internal model or product surface, authenticate the underlying model identity, or establish that a public case is unseen. The CLI invocation and complete trace are retained locally. The experimental local launcher is not presented as a portable, validated benchmark adapter.

## Grader learning

The original 0.2.0 grader compared downstream location strings literally. It rejected quoted sheet names even when they referred to the same Excel cells. This was a scoring defect, not a reason to modify or retry the candidate's answer.

Grader 0.2.1 compares equivalent scalar Excel addresses, including quoted sheet names, escaped apostrophes, absolute anchors and case. Wrong locations, external workbooks and ranges remain distinct. Regression tests cover both accepted equivalents and rejected mismatches. The exact original response and its initial grade are preserved; explicit regrading produced a second revision under 0.2.1.

## Review status

The capture is completed, its grade is provisional, and successful-audit status remains null. A metadata-blinded human-review packet with blank decisions is prepared locally. No human verdicts have been supplied. The answer, raw tool trace and unfinalized scores are excluded from the public source and release archive. The published viewer report still contains only labeled simulated fixtures.

Next: review the reference and captured answer with a human, test more configurations/cases under frozen settings, and investigate helpful and harmful revisions. One smoke attempt supports workflow debugging; it provides no success rate, comparative ranking or general finance-capability claim.
