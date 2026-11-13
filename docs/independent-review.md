# Independent authoring QA

This review was performed by a separate AI authoring agent with full access to reference answers. It is independent of the workbook builder at the task level, not independent human expert validation and not a blind performance evaluation. No model capability score follows from it.

## Checks performed

The reviewer inspected XLSX XML formulas and cached values directly with Python's standard library. It independently recomputed 50 original-case forecast values with Decimal arithmetic from the stated scenario assumptions; all matched reference caches within 0.00000001 in source units. It also compared root dependencies, reference outputs, planted impacts, and formula differences against all four current manifests. These are checks of exported files and arithmetic, not native Microsoft Excel recalculation.

| Case | Exact formula changes | Verified root output, correct versus altered | Verified propagation |
| --- | --- | --- | --- |
| case-001 | Operating Model!I39 only | 15.4286055 versus 20.1493215; original minus correct +4.720716 | I40 FCF margin; I42:L42 cumulative cash flow |
| dev-002 | Debt Schedule!G20 only | 10.35 versus 12.15; original minus correct +1.80 | G22 coverage; G24:I24 cumulative interest |
| dev-003 | Valuation!G21 only | 369.5 versus 293.5; original minus correct -76 | G24 value per share: 8.797619047619047 versus 6.988095238095238 |
| dev-004 | No formula changes | Clean control | No planted formula error |

All manifest base-probe inputs match root dependencies in the reference workbook caches within 0.00000001. Correct arithmetic was independently checked:

- Working capital: 20.0550735 + 4.53222 - 6.79833 - 2.360358 = 15.4286055. Adding instead of deducting the working-capital increase overstates cash flow by twice that increase.
- Debt: average opening/closing debt (135 + 95) / 2 = 115; interest = 115 × 9% = 10.35. Opening debt alone gives 12.15. The equal-debt probe is deliberately nondiscriminating; the increasing-debt probe reverses the direction of the original mistake.
- Valuation: 484.5 - 125 - 20 - 17 + 38 + 9 = 369.5. Subtracting the 38 of cash rather than adding it understates equity value by 76. Zero cash is deliberately nondiscriminating; the nonzero-cash perturbation catches the wrong sign.

## Probe and grader evidence

`tests/test_grading.py` includes controlled submissions generated from the actual manifests. Every canonical repair passes all three numerical probes. Every planted wrong repair, expressed using supported arithmetic, fails at least one probe. The clean submission passes deterministic checks. All remain provisional without human adjudication.

The restricted evaluator accepts arithmetic and selected scalar functions, not general Excel syntax. The reference workbook may use SUM ranges even when an algebraically equivalent direct formula is used by the manifest. Range, cross-sheet, or other unsupported candidate formulas route to human review. Matching the canonical formula string alone does not establish correctness. Three finite probes cannot establish universal functional equivalence or prove correct dependency behavior under every possible input; explicit explanation and restraint adjudication are still required.

Security/correctness fixtures cover malformed objects, refusals, bad numeric types, booleans, NaN, infinity, enormous integers, bounded formula complexity, unsafe syntax, hardcoded repairs, base-input overfitting, equivalents, missed errors, false positives, conflicting duplicate repairs, clean cases, and downstream symptoms.

## Scoring interpretation and remaining human work

`diagnosis_required` supplies the reference concept to the adjudicator; the grader does not pretend to establish semantic diagnosis by exact text matching. Human `detection:<error-id>` and `explanation:<error-id>` verdicts must cite evidence from the original answer. Human `restraint` assesses all proposed changes, including suggestions the submission labels nonmaterial. Numeric passing alone never finalizes audit success.

Duplicate root locations do not increase recall or precision; conflicting repairs at the same root fail. A downstream-only symptom without its own repair is associated with the root rather than counted as a separate false positive. A separate proposed downstream repair counts as a potential material extra and requires review; legitimate alternative repair strategies should be adjudicated transparently rather than silently forced through this simple location-matching track.

Numerical impact accuracy counts two required outputs per error: corrected value and original-minus-correct impact. Missing either contributes a failure for that output. Propagation is separate from primary success. Root recall and precision are labeled provisional because exact root-cell matching is only an initial candidate match.

Malformed/refused/incomplete responses are unsuccessful attempts, never successes or silently excluded runs. The runner must retain them in the primary denominator. Unadjudicated attempts have unknown final success and must remain visibly pending rather than converted into passes. Infrastructure failures require their own predeclared handling. Cases with no findings have undefined finding precision, rather than an invented 100% precision.

Before public capability findings: complete human review of every first-release attempt, verify run isolation and configuration records, and report native Excel limitations. The current public development fixtures are excluded from headline hidden-test scores.
