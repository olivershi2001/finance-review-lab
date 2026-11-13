# Human review packets

The scorer cannot verify that an operator is human or that their judgment is correct. This workflow records explicit human attestation, evidence and artifact binding; it never supplies real review decisions automatically. Unit tests use simulated decisions and must not be published as human-reviewed performance.

## Prepare a packet

Run from the repository root with a captured structured response and its frozen manifest:

```sh
python -m frl.review prepare --response runs/example/analyst/response.json --manifest references/case-001/manifest.json --review-id blind-017 --output work/review-blind-017
```

Use an opaque ID without configuration/model information. The packet includes `review.html` and `worksheet.json`. Only the response, manifest and opaque ID are accepted by the generator; run metadata is not included. The structured answer is rendered using its exact JSON values, with HTML escaping, alongside deterministic evidence and pending criterion prompts. Preserve and inspect the captured raw response separately where exact original prose/formatting matters.

This is metadata blinding, not guaranteed anonymity: answers may name their model or product, and wording can reveal a configuration. A separate coordinator should keep the review-ID-to-run mapping away from the reviewer when practical. Do not call this independently blinded human grading if the same person authored the cases, ran the models and knows the mapping.

## Review

Open the HTML report. Inspect the workbook, reference conventions, original answer and proposed repairs. In `worksheet.json`, the reviewer must fill:

- `reviewer_kind`: `human` only when a human actually performs the review.
- `reviewer`: a stable reviewer name or pseudonym.
- Every pending criterion: boolean `verdict` and nonempty `evidence`.

Leave null decisions pending until reviewed. Evidence should quote the relevant answer span or explicitly identify an omission, then explain the decision. A reference answer alone is not evidence that the model detected it. For restraint, inspect all suggestions, including ones the model labels nonmaterial. Unsupported formulas require actual spreadsheet checking or explicit financial equivalence analysis; finite probe matching is not proof of general Excel equivalence.

The reviewer should fail detection/explanation when a model merely names the right cell without explaining the material error. Root locations, numerical values, repairs and restraint are separate criteria. Missing/invalid/refused attempts remain failures and are not converted into successful audits through human review.

## Finalize and grade

```sh
python -m frl.review finalize --response runs/example/analyst/response.json --manifest references/case-001/manifest.json --worksheet work/review-blind-017/worksheet.json --output work/review-blind-017/adjudication.json
python -m frl grade example analyst --adjudication work/review-blind-017/adjudication.json
```

Finalization rejects missing human attestation, unfinished decisions, missing evidence, altered criterion sets, and changed response/manifest contents. Hashes use canonical parsed JSON rather than raw-file formatting; whitespace-only JSON changes do not invalidate the packet. Original byte integrity remains the run manager's responsibility. Existing packets and finalized files are not overwritten.

The run manager validates bound worksheets again when grading and when reproducing a report. A worksheet from another answer or manifest is rejected even if its individual criterion verdicts look valid. Legacy direct criterion maps remain readable for old captures and software fixtures; they do not provide packet-level binding or human-identity attestation.

Human adjudication cannot turn a repair that demonstrably fails probes or simply hardcodes an output into a valid repair. Escalate disputed reference defects through case invalidation/versioning rather than quietly changing a score. Record disagreements and a second reviewer when available.

## Interpretation

A completed packet is an attributable decision record, not proof of independent expert review. The benchmark currently has authoring QA and simulated grading fixtures, not actual human-reviewed model scores. The restricted parser routes exponentiation to review because Python and Excel have different precedence/associativity conventions. Ranges and cross-sheet formulas also require review; it is not a general Excel engine.
