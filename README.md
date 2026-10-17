# EcoMind AI

Explainable environmental-intelligence agent built on **FalkorDB** (FalkorDB Graph Hackathon · track: *Agents That Act on Connected Data*). Creator: Lojain Hany.

It answers a question such as *"How can our school reduce waste most effectively?"* by running fixed, validated Cypher queries, following multi-hop causal chains (`Cause → Cause → Problem`), ranking interventions with transparent configurable weights, and showing every query, relationship and missing piece of evidence.

> **Data warning:** the school-waste scenario is **synthetic** (fictional "Greenfield School"). Weights, costs and "evidence" are illustrative assumptions, not measurements.

## Status (honest)
| Item | State |
|---|---|
| Engine, API, validation, UI code | Written; 20 offline tests pass (using a **test double**, not FalkorDB) |
| Real FalkorDB queries | **Not yet run by the author of this code** — the build sandbox had no Docker/network. The 5 integration tests are skipped there. Run them (below) before claiming integration. |
| LLM narration | Written, untested (no API key/network). Deterministic template is the default and is labelled in the UI. |

## Quick start
```bash
docker compose up -d                      # FalkorDB on :6379 (browser on :3000)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # optional; defaults work locally
python -m ecomind.seed                    # builds the synthetic graph
python -m unittest discover -s tests -t . -v   # integration tests now run for real
python -m ecomind.server                  # open http://127.0.0.1:5000
```
Optional LLM narration: put `ANTHROPIC_API_KEY` in `.env` (never commit it). Without it the UI shows `[deterministic-template]`.

## Layout
```
ecomind/  config.py  seed_data.py  queries.py  db.py  engine.py  llm.py  server.py  seed.py  static/index.html
tests/    test_queries.py  test_engine.py  test_api.py  test_falkordb_integration.py  fakes.py
docs/     ARCHITECTURE.md  SCHEMA_AND_QUERIES.md  DEMO_SCRIPT.md  SUBMISSION.md
```

## Security
No endpoint accepts Cypher. User text only selects a problem id by keyword; all queries are a fixed whitelist with validated parameters (`^[a-z][a-z0-9_]{1,63}$`), run read-only (`ro_query`). Secrets come from environment/.env (git-ignored).

## Troubleshooting
- *"Cannot reach FalkorDB"* → `docker compose ps`; check `FALKORDB_HOST/PORT`.
- *Integration tests skipped* → the server isn't reachable or `falkordb` isn't installed.
- *Cypher syntax error on a query* → run it in FalkorDB Browser (:3000); versions differ. Report it — see docs.
- *"No matching problem"* → include a keyword like "waste" or "recycling".

## Limitations
Single synthetic scenario; keyword routing (not NLU); scoring weights are heuristics; only degree-style graph analysis (`driver_fanout`) is used — FalkorDB's built-in algorithms (e.g. PageRank) are not used yet; no real data ingestion.

License: MIT.
