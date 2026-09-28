# Synthetic feasibility results

| Validator | TP | FN | FP | TN | Precision | Recall | Valid acceptance |
|---|---:|---:|---:|---:|---:|---:|---:|
| contracts_strict | 384 | 96 | 48 | 192 | 88.9% | 80.0% | 80.0% |
| excerpt_baseline | 96 | 384 | 48 | 192 | 66.7% | 20.0% | 80.0% |
| always_accept | 0 | 480 | 0 | 240 | n/a | 0.0% | 100.0% |
| always_reject | 480 | 0 | 240 | 0 | 66.7% | 100.0% | 0.0% |

720 cases, 48 shared scenario groups, seed 1729.

These are construction checks and scope challenges, not evidence of real-world LLM accuracy.

Corpus SHA-256: `be233d8434d49e7b07f5291ddaec4072289b0f9bb0d2d335237b844bac1813ea`
