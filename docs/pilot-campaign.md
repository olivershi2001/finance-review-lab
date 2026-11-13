# Manual pilot campaign

The campaign planner freezes a queue; it does not execute a model, automate subscriptions, or create performance results. Four public development cases × two user-supplied configurations × three repetitions produce 24 initial trials. These remain development evidence, excluded from headline benchmark claims.

## Record configurations first

Create two JSON files using actual model/product names selected in your interfaces. Record settings as observed; use `"unknown"` for unavailable setting values. Do not infer hidden reasoning settings. Required structure:

```json
{
  "model": "REPLACE WITH SELECTED MODEL",
  "product": "REPLACE WITH PRODUCT",
  "date": "2026-11-06",
  "settings": {"reasoning": "unknown"},
  "tool_access": ["workbook formula inspection"],
  "attempt_cap": {"max_seconds": 1200, "max_interactions": 8},
  "infrastructure_retry_policy": {
    "max_retries": 1,
    "only_confirmed_infrastructure": true
  }
}
```

The example is deliberately rejected until placeholders are replaced. Cap values are proposed operator choices, not measured response times. Agree on them before freezing. Both configurations should have comparable tool access, caps, and retry rules unless the explicit research question tests those differences.

From the repository directory:

```sh
python3 -m frl.campaign plan pilot-v1 --config config-a.json --config config-b.json
python3 -m frl.campaign status pilot-v1
python3 -m frl.campaign init-next pilot-v1
```

Global `--root PATH` comes before the command. `plan` supports `--seed 1729`, `--repetitions 3`, and optional `--branches`. Queue order is seeded and blocked: each case/repetition pair runs both configurations in randomized order. Run IDs are unique and deterministic. Different campaign IDs create separate runs; never relabel repeats as the same attempt.

## Frozen artifacts

`campaigns/<id>/plan.json` contains case versions, dataset/reference hashes, configurations, caps/retry policies, prompt hashes, planned stages, and queue order. Its canonical-content SHA-256 detects accidental changes. Configuration copies, prompt copies, and blind ZIPs are stored alongside it. All operations validate the freeze. Hashes provide integrity checks, not signatures against a malicious operator editing all records.

Only upload the returned case blind ZIP to an isolated fresh session. It contains workbook, task, sanitized metadata, and standardized analyst prompt. Never upload the campaign directory, reference files, or this authoring checkout. Optional reviewer prompts live separately; transfer the original analyst answer to the independent reviewer, then transfer reviewer feedback to a branch from that same initial answer. The CLI capture layer enforces original-answer parent hashes.

`init-next` initializes the first uninitialized trial using the ordinary run-management API and returns its package location. It does not start a chat. It may initialize another trial while earlier ones await answers; `status` makes unfinished work explicit. Planned stages without captures are `pending`; absent optional stages are `not_planned`. A created run is `initialized`; captured analyst statuses remain `completed`, `refused`, `malformed`, `incomplete`, or `infrastructure_failure`. Completed means captured, not successful or adjudicated.

Import and grade responses with the commands in [run-guide.md](run-guide.md). Preserve elapsed seconds, interaction count, raw answers, refusals and failed attempts. The planner does not schedule retries: confirmed infrastructure failures remain recorded and any manual retry must follow the frozen policy, use a distinct run ID, and reference the original failure in the operator note. Never retry a substantive wrong answer or silently remove an attempt.

No default campaign is instantiated in the repository: real configurations and operator-approved caps must be supplied first. Tests use temporary synthetic configuration fixtures, not real model results.
