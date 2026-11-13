# Maple Equipment: model audit

Audit the attached model.xlsx for material formula errors. Review the operating forecast and unlevered cash-flow calculations. Treat supplied inputs as authoritative and use the conventions on Assumptions. There may be zero, one or multiple errors. Do not replace stated conventions with preferred practices.

For each genuine root cause, identify the sheet and cell, quote the existing formula, explain the error, provide a corrected live Excel formula, quantify its impact and list affected downstream cells. Group symptoms under their root cause. Leave correct work unchanged.

Return an audit memo and a JSON object with a findings array. Each finding must contain sheet, cell, existing_formula, diagnosis, corrected_formula, correct_value, original_minus_correct, downstream_cells and explanation. Monetary amounts are USD millions, except an explicitly per-share output. Use at least four decimals for numerical impacts. For no material errors, return {"findings": []} with a short explanation.

Only this brief and model.xlsx belong in an evaluation session. Do not access reference assets or public answer keys.
