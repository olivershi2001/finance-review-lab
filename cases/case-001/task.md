# Cedar Industrial Supply: model audit

Cedar Industrial Supply is a fictional distributor. The attached `model.xlsx` contains 2023–2025 historical financial data and a 2026–2030 operating and unlevered cash-flow forecast. All amounts are USD millions, with no rounding of underlying calculations.

Audit the workbook for material formula errors. Treat the supplied historical financial data and forecast assumptions as authoritative. Apply the conventions documented on Assumptions. Debt, interest, a full balance sheet, and detailed fixed-asset depreciation are outside scope. Do not substitute your own forecast or accounting convention.

For each genuine error, provide:

1. The sheet and exact root-cause cell.
2. The existing formula and an explanation of the mistake.
3. A corrected Excel formula.
4. The affected year's correct free cash flow and the original overstatement or understatement.
5. Other outputs affected by the same root cause.

Report downstream effects together with their root cause rather than as separate errors. Leave correct formulas unchanged. There may be zero, one, or multiple errors. Passing existing checks does not establish that the entire workbook is correct. Formatting improvements are not material formula errors.

Return a concise audit memo and a JSON object in this format:

```json
{
  "findings": [
    {
      "sheet": "sheet name",
      "cell": "A1",
      "existing_formula": "=...",
      "diagnosis": "explain the financial error",
      "corrected_formula": "=...",
      "year": 2026,
      "correct_fcf": 0,
      "original_minus_correct_fcf": 0,
      "downstream_cells": ["Sheet!A1"],
      "explanation": "show calculations"
    }
  ]
}
```

Use numeric values in USD millions, to at least four decimals. The example's year, address and zero values illustrate the schema only.

Only this brief and `model.xlsx` belong in the evaluation chat. Do not supply the repository, reference workbook, expected values or scoring documents.
