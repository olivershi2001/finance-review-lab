# Case 001 reference answer — do not provide to the evaluated model

## Root cause

`Operating Model!I39` adds the 2027 increase in net working capital rather than subtracting it.

- Submitted formula: `=SUM(I35:I36)-I37+I38`
- Reference formula: `=SUM(I35:I36)-SUM(I37:I38)`
- Equally valid repair: `=I35+I36-I37-I38`

2027 change in NWC is $2.360358m. Correct FCF is $15.4286055m, compared with submitted FCF of $20.1493215m. The overstatement is $4.720716m, twice the NWC increase.

2027 FCF / revenue is overstated. Cumulative forecast FCF is overstated by $4.720716m in each of 2027–2030 (`I42:L42`). Annual FCF in 2028–2030 is unaffected.

The four existing checks continue to pass because none tests the FCF bridge. This limitation is disclosed in both versions. The source assumptions explicitly state the working-capital convention. This is intentionally an easy workflow-validation case, not a challenging capability benchmark.

## Scoring

Record five separate binary criteria rather than relying solely on a composite:

1. **Detection:** identifies I39 as the root cause and explains the wrong working-capital sign.
2. **Repair:** supplies a live formula equivalent to NOPAT + D&A − capex − increase in NWC, referencing the correct cells. Hardcoded answers are not valid repairs.
3. **Magnitude:** gives correct 2027 FCF within $0.0001m and the $4.720716m overstatement within $0.0001m.
4. **Propagation:** identifies I40 and I42:L42 without claiming that subsequent annual FCF is wrong.
5. **Restraint:** proposes no material changes to correct logic or authoritative assumptions.

Primary successful-audit outcome requires criteria 1, 2, 3 and 5. Report propagation separately. A numerical-only grader cannot establish detection, valid formula semantics or restraint: a human must adjudicate those criteria. Alternate Excel syntax is allowed. Do not count downstream symptoms as additional independent findings. A proposed optional stylistic enhancement is not a false positive unless described as a material error or applied as a required repair.

The reference's correct workbook is `reference.xlsx`; `expected.json` records independently calculated forecast outputs. This package contains no measured AI performance.
