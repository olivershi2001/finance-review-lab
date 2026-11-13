# Authoring an original case

Cases are authored evaluation artifacts, not evidence of a source company's mistakes. Current development inputs are synthetic. Do not use employer materials, proprietary models, or undocumented copied examples.

1. Specify an economically meaningful relationship and explicit conventions. Choose units, periods, signs, interest convention, tax treatment, rounding, and required outputs before authoring errors.
2. Build the correct workbook first. Separate blue numeric inputs, black same-sheet formulas and green cross-sheet formulas. Use restrained headings, consistent years, readable widths, frozen panes, hidden gridlines and landscape print settings. Keep formulas live.
3. Independently calculate outputs without copying the workbook formulas verbatim. State what is simplified; do not label a partial cash-flow schedule a complete three-statement model.
4. Copy the correct workbook and alter only the intended formulas. Root causes are conceptual errors, not every downstream symptom. Make clean controls using legitimate explicit conventions. Never disclose error counts or control status in blind materials.
5. Record an error manifest and a rubric. Include exact locations, accepted financial logic, base calculations, at least two meaningful perturbations, impact tolerances in source units and downstream effects. An empty error list is required for a clean control.
6. Check style parity, all cell/formula differences, external links, comments, metadata, hidden content, output propagation, errors and circularity. Render every sheet. Record unavailable native Excel tests explicitly.
7. Package only task material for the evaluated session. Keep builders, manifests, reference answers and validation logs outside its filesystem access. Public development answers are deliberately public and cannot be called unseen.
8. Freeze versioned artifacts and hashes before collecting scored attempts. Correct a defective case by issuing a new version and documenting invalidated runs; never silently edit scored data.

## Financial and grading review

Perturbations should distinguish a genuine dependency-preserving formula from a memorized number or accidental match. Test boundary assumptions where relevant. Supported arithmetic checks are evidence for a proposed repair, not a general-purpose Excel calculation engine. Unsupported formulas and judgment about diagnosis, materiality, symptoms and false corrections require evidence-bearing human review.

Check wrong answers as seriously as correct answers: a grader must not reward hardcodes, duplicate symptoms, an incorrect repair, or an overzealous correction of a clean model. Single-author review is not independent expert validation.

## Private evaluation isolation

Create private evaluation assets outside the public checkout and establish fresh, restricted evaluation contexts before running them. An ignore rule alone is insufficient. An agent involved in authoring a case cannot be counted as a blind evaluated model. Public development cases may validate operations but do not enter headline scores. The planned twenty-case private set is not complete merely because its inventory exists.

## Rebuilding the shipped development workbooks

The builders require a separately available `@oai/artifact-tool` Node runtime. It is not included in the source archive and is not needed to run evaluations or verify the shipped workbooks. Use its documented environment setup rather than installing an unrelated package with a similar name.

With that runtime available, run from the project root:

```sh
node scripts/build-case-001.mjs
node scripts/build-development.mjs
python3 scripts/prepare-cases.py
python3 verify_suite.py
```

The builders calculate and export the workbooks and render previews into ignored build-previews/. prepare-cases.py adds native print metadata, constructs grading manifests and records final hashes. It does not change financial formulas. Rebuilding intentionally changes the artifact snapshot and must happen before starting a new run; existing runs freeze old hashes and should not be retroactively modified.

Review every new preview and record the result before releasing rebuilt artifacts. Do not infer visual quality solely from a successful script. The saved-file verifier does not execute Excel formulas; it compares caches to an independent financial calculation and inspects formula structure. Live assumption-change tests run in the authoring engine. Neither substitutes for native Excel validation.

To prepare empty external private-workspace infrastructure, run `python3 scripts/init-private-workspace.py DESTINATION` with a new directory outside this checkout. This creates no tasks and establishes no access isolation by itself.
