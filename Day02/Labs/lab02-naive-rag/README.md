# Lab 2 — Embeddings & Naive RAG

**AskIT today:** finds the right Orbit KB article for a question and answers from it — with sources, or "I don't know".

| Part | File | Time | Challenges |
|---|---|---|---|
| **A** | `lab02a_embeddings.py` | 40 min | Challenge 1, 2, 3 (+ stretch) |
| **B** | `lab02b_index.py` | 40 min | Challenge 4, 5, 6 (+ stretch) |
| **C** | `lab02c_rag.py` | 40 min | Challenge 7, 8, 9 (+ stretch) |

Parts are independent — if you're stuck in A, you can still do B and C.

## How to work
1. Open the file in VS Code, find `TODO-n`, follow the hints.
2. Run it: `python Day02\Labs\lab02-naive-rag\lab02a_embeddings.py`
3. Check yourself: `pytest Day02\Labs\lab02-naive-rag` → aim for **9 passed**.
4. End of class: **🏁 Day End** in the session page.

## Lab A — embeddings (`lab02a_embeddings.py`)
| # | Do | Test |
|---|---|---|
| Challenge 1 | TODO-1: call Titan Text Embeddings v2 with `client.invoke_model(...)` | `test_challenge_1` |
| Challenge 2 | TODO-2: cosine similarity | `test_challenge_2` |
| Challenge 3 | TODO-3: top-k most similar, then **run the script** | `test_challenge_3` |
| ⭐ Stretch | Re-run with `dimensions=256` and `1024`. Do the top-3 KB matches change? | — |

## Lab B — your own index (`lab02b_index.py`)
| # | Do | Test |
|---|---|---|
| Challenge 4 | TODO-4: overlapping word chunks | `test_challenge_4` |
| Challenge 5 | TODO-5: build the index (id, doc_id, text, vector) | `test_challenge_5` |
| Challenge 6 | TODO-6: search, then **run the script** → hit rate @3 | `test_challenge_6` |
| ⭐ Stretch | Try `size=40`, `80`, `200`. Record the hit rate for each in `submission\stretch_chunking.md`. | — |

## Lab C — RAG (`lab02c_rag.py`)
| # | Do | Test |
|---|---|---|
| Challenge 7 | TODO-7: grounded prompt — context with [KB ids], rules, question | `test_challenge_7` |
| Challenge 8 | TODO-8: retrieve → prompt → answer | `test_challenge_8` |
| Challenge 9 | **Run the script.** Test checks AskIT cites sources and says "I don't know" for questions not in the KB | `test_challenge_9` |
| ⭐ Stretch | Try `k=1` and `k=6`. Which answers break? How many more input tokens? | — |

First run of Lab C builds the KB index (~1 min) and caches it in `index\` (not pushed).

## Stuck?
| Symptom | Fix |
|---|---|
| `AccessDeniedException` on Titan | Titan Embeddings v2 not enabled for your user — tell the trainer |
| `ThrottlingException` | The whole class is embedding at once — wait 30 s, re-run |
| Test 9 fails on "I don't know" | Make the rule in TODO-7 explicit: reply exactly with the `IDK` text |
| Test 9 fails on citations | Label each chunk `[KB-00X]` in the context and ask for citations |
