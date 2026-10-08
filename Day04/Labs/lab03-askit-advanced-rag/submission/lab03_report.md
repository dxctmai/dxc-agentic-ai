# Lab 3 report

## 1. Eval results
Copy from the 📊 Evals dashboard (**Latest run per configuration**).

| Configuration | pass rate | hit@1 | MRR | wrong source on top |
|---|---|---|---|---|
| Baseline (naive RAG) | 0.471 | 0.533 | 0.656 | 3 |
| + Metadata filter | 0.765	| 0.733 | 0.756 | 0 |
| + Section chunks + hybrid | 0.941	| 0.933 | 0.967 | 0 |
| FDE-grade (all on) | 0.941 | 0.933 | 0.967 | 0 |

**The biggest lift came from:** FDE-grade (all on)

## 2. Security check — the poisoned article
**Question I asked:** TODO

**Baseline followed the hidden instruction? (yes / no):** TODO

**FDE-grade followed it? (yes / no):** TODO

**One more defence I would add in production:** TODO
