# Alpha a2 release pilot — frozen before collection

This is an engineering pilot, not a preregistered accuracy study. Human review is
an optional future validation stage, not a release gate. No LLM judge supplies labels.

## Collection, fixed in advance

- Two local model families: `qwen3:1.7b` and `gemma3:1b`, exact installed digests
  and model templates recorded in the manifest. No remote paid API.
- Sixteen authored, fictional scenarios: customer support and interactive fiction,
  English and Spanish, four balance settings each. Eight families group language/model
  variants; these are not 32 independent scenarios or production sessions.
- One output per model/scenario: 32 requests. No retries, selection by verdict, repairs,
  prompt tuning on the outputs, or omission of malformed/truncated responses.
- Temperature 0, seed 1729, 4096 context, 512 output-token cap; Ollama JSON output mode.
  Thinking disabled if the model advertises that capability. Keep prompts/settings.
- Trusted scenario states fixed by the application. Models produce prose and declared
  branch claims; do not derive reference state from model output.
- Freeze this protocol, prompts, profile and scenarios in a hashed manifest before
  first generation. Record all responses and failures, token usage and elapsed time.

## Analysis

Replay with exact declared-claim consistency, minimum tokens/diversity, lexical
restatement and formula matching. Report invariant-only and heuristic-only profiles
and a simple character-length assertion comparator. Count structural failures,
missing attempts, unknowns/errors, findings, acceptance and latencies. Profile
acceptance is **not accuracy**; no natural semantic precision/recall or model-quality
ranking is identified without independently justified labels. Typed claims do not
certify arbitrary prose. Infrastructure/power costs are unmeasured, even when API fees are zero.

Synthetic mutations stay separate, with operator-authored labels, exclusions,
attributed detections, survivors and valid controls. No test-driven threshold changes
on this pilot. Public weights are not redistributed. Publish fictional prompts and raw
model outputs, the deterministic replay command and environment information.

Replaying stored outputs must reproduce reports/summary byte-for-byte with the pinned
library version. Regenerating may differ by hardware/runtime despite fixed seed.
The full independent-study protocol is future work in `protocol.md`.
