# Native Excel QA

Observed November 6, 2026 in Microsoft Excel for Mac. Disposable copies were opened through the native application UI, Calculate Now was clicked, and saving was confirmed. Shipped source workbooks were not replaced by Excel's rewritten copies.

All eight case/reference workbooks matched across 908 formula caches at an absolute tolerance of 0.00000001. The comparison also checked existing formulas, input values and text. Excel saves repeated formulas as shared formulas and removes optional quotes from simple sheet names; the verifier expands shared A1 references before comparing. The machine-readable report records both source and native-saved hashes. This is an observed authoring validation, not an independent certification or a model result.

A disposable dev-002 reference was tested with Assumptions!G14 changed from 9% to 0%. After native recalculation and save, Debt Schedule!G20 was zero and G22 was the text `n.a.`. The unmodified baseline was preserved before this change. Other input boundaries were tested in the authoring engine, not natively repeated here.

## Printing and layout

Native print preview exposed an orphaned check on a second page in dev-003. The three newer cases now use 19-point populated rows and 6-point empty spacers. Text remains at the authored font size. Rebuilt reference previews were visually inspected for all six affected sheets.

Entire Workbook preview was then inspected in Excel for dev-002, dev-003 and dev-004: each showed two A4 landscape pages for two sheets, with the main schedule and its checks together. Printing to a physical printer was not tested. The original three-sheet case's native printed-page layout remains unverified. Audit/reference style parity is separately checked; these observations do not establish every printer, paper setting or Excel version.

## Recheck saved copies

After making and natively recalculating disposable copies, run:

```sh
python3 scripts/verify-native-excel.py --native-directory PATH_TO_COPIES --output reports/native-excel-validation.json
```

Use filenames `<case-id>-cases.xlsx` and `<case-id>-references.xlsx`; the debt reference baseline is `dev-002-reference-native-base.xlsx` and the zero-rate copy is `dev-002-zero-rate-native.xlsx`. The verifier compares saved evidence. It does not automate Excel or independently prove that Calculate Now was clicked. Native copies and UI logs stay outside the source release. Tests check that the recorded source hashes still match the shipped assets; workbook edits require renewed native QA.

`verify_suite.py` performs the independent arithmetic/XML checks and does not itself run Excel. Its `native_excel_verified: false` field describes that command's scope; the separate native report records the observed application check.
