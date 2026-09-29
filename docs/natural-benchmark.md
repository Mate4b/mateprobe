# Real-model pilot and deterministic replay

> Historical evidence/reference from Narrative Contracts. The current project is
> **MateProbe by Mate4B**; see the [migration guide](migration-mateprobe.md).
> Original package names, versions and recorded results below identify that earlier work.

This pilot uses actual locally generated outputs from Qwen3 and Gemma3 on fictional,
authored scenarios. It is distinct from synthetic mutations and from production traffic.
The frozen design is in [release-protocol.md](../paper/release-protocol.md).

The manifest pins model-weight digests, quantization, runtime version, prompts, generation
settings and scenario groups. `outputs.jsonl` keeps every request/response, malformed output,
truncation and provider failure; there are no repairs or retries. Exact natural-language
regeneration is not promised across hardware/runtime versions. The deterministic claim is
about replaying **stored inputs** through a pinned evaluator.

```sh
python benchmarks/natural.py replay \
  --input benchmarks/natural-results --output /tmp/natural-replay
```

Compare `reports.json` and `summary.json` with `benchmarks/natural-results/evaluation/`.
These files must match byte-for-byte with the pinned library version. `latency.json`
is deliberately separate because timing varies. No Ollama installation is needed for replay.

For an entirely new collection, install Ollama, download the two models, start its server,
and use a new output directory. This downloads model weights and uses your local hardware:

```sh
ollama pull qwen3:1.7b
ollama pull gemma3:1b
python benchmarks/natural.py collect --models qwen3:1.7b gemma3:1b \
  --output /tmp/my-natural-collection --base-url http://localhost:11434
```

The collector alone uses HTTP; neither the library nor the pytest plugin does. Model metadata
and weights belong to their upstream providers; weights are not redistributed. Protocol,
prompts and benchmark harness are authored here. Raw outputs are supplied for evaluation and
are not human-approved recommendations.

Collection runs all scenarios for one model before moving to the next. Use an otherwise
idle Ollama server and avoid other clients during the run. The collector checks `/api/ps`
before each batch, explicitly unloads its model with `keep_alive: 0` afterward (including
on exceptions), and verifies the server is empty before proceeding. An unload failure or
a model still resident stops collection; recorded attempts remain on disk. Existing models
belonging to other work are not unloaded automatically. These checks cannot prevent another
client from concurrently loading a model. See Ollama's [running models API](https://docs.ollama.com/api/ps)
and [generation API](https://docs.ollama.com/api/generate).

## Reading the results

- Denominator: every requested generation. Structure/truncation failures are not dropped.
- Exact invariants check supplied typed declarations against their own branch state.
- Heuristics check token floors, formula patterns and lexical overlap.
- Invariant-only/heuristic-only ablations and a simple character-length assertion are reported.
- Acceptance is not accuracy, preference or prose truth. Correct declarations can accompany
  incorrect prose. No natural semantic precision/recall, FPR/FNR or superiority claim follows.
- Model requests share scenario families. Different languages and models are related samples.
- Provider fees are zero for local generation; power, hardware and maintenance costs are unmeasured.

Ollama's [generation API](https://docs.ollama.com/api/generate) documents JSON mode, token
counts, sampling options and thinking controls. Model descriptions are available for
[Qwen3 1.7b](https://ollama.com/library/qwen3:1.7b) and
[Gemma3 1b](https://ollama.com/library/gemma3:1b). Results describe these exact small quantized
models and this workload, not their whole families or the wider industry.


## Captured collection

32 responses were retained. Qwen3 produced 16 structurally valid envelopes and all 16 passed
its declaration-only profile, while none passed the strict/heuristic profiles: all 32 outcome
bodies triggered the lexical-content floor, and eight restatement findings were recorded.
Gemma3 produced 16 responses with invalid envelopes; none entered text-contract evaluation.
These are findings and request counts, not counts of independently confirmed semantic defects.
There were no missing requests or collection errors. These outcomes are not a model ranking.

`collector-source.py.txt` preserves the exact source whose hash was frozen at collection.
The release collector subsequently omits a local absolute path in Ollama's `modelfile`
metadata; the published manifest records that redaction. Model weights, templates, parameters,
requests, responses and rule configurations are unchanged. Evaluation is replayed with a2
(package-version metadata updated; rule semantics unchanged).
