# Expanded synthetic mutation campaign

This authored campaign separates state invariants from text heuristics.
It is not a natural-output semantic-accuracy study.

Corpus SHA-256: `cfad3ba2aca7b31418dfe3d39d785c2ddc22203975a3a29e7a374d0e8264c255`

| Scope | Cases | Faults | Detected | Detection | Controls | Preserved | Preservation |
|---|---:|---:|---:|---:|---:|---:|---:|
| invariant | 7 | 5 | 4 | 0.8 | 1 | 1 | 1.0 |
| heuristic | 14 | 8 | 4 | 0.5 | 4 | 3 | 0.75 |

Survivors and false positives are retained as evidence about the configured guarantees.
Equivalent and not-applicable/unreviewed labels are excluded from denominators.
