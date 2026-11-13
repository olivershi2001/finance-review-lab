# Provenance and limitations

Version 0.2.0. Four public development examples, original synthetic scenarios. All financial assumptions were authored for fictional businesses. No employer information, work-machine skill, deal material, Mercor task, external benchmark question or real-company filing is incorporated.

Workbook builders use OpenAI Artifact Tool. The shipped workbooks and dependency-free Python verifier are sufficient to inspect and reproduce validation. Rebuilding requires separate access to that optional authoring runtime, which is not redistributed.

manifest.json records case version, split, source type, units, root causes, probes, numerical impacts, downstream cells and workbook hashes. validation.json records saved-file checks. authoring-validation.json, when present, records live input perturbations. The original case's input change test is documented in its builder and the separate review. Formatting inspection is recorded in progress.md.

The authoring context has seen the answers. A separate AI agent checked calculations, probes and scoring tests while sharing the authoring filesystem. This is implementation QA, not independent human validation, blind performance or evaluator isolation.

No independent model trials have been conducted. The bundled report is constructed test data. Its apparent model, answers, failures and adjudication records are explicitly simulated. It contains no measured model performance, real human verdicts or compute-cost measurements.

Native Microsoft Excel recalculation was observed on eight disposable baselines, with 908 cached formulas matching the sources and one zero-interest input boundary checked. Six sheets across the three newer cases were inspected in native whole-workbook print preview. See native-excel-qa.md for exact coverage and limits; authoring-engine checks alone do not establish native equivalence. The formula checker supports limited Excel arithmetic; unsupported functions, ranges and cross-sheet repairs need evidenced review. Finite probes may miss intentionally overfit formulas.

The cases are deliberately small. Three have one planted root cause; the control has none. The planned twenty-case private benchmark is not included. A separate directory alone does not isolate a shared-context evaluator.

If public filings or external datasets are added, record per-asset sources and reuse rights separately. This project's synthetic-data license does not extend to third-party assets.
