# Architecture
```
Browser UI (SVG graph, recommendations, evidence inspector, query trace)
   │  POST /api/investigate {question, weights}
Flask server ── validates JSON ──► Engine
                                   1 route question → problem id (keywords; never Cypher)
                                   2 run whitelisted queries via GraphStore (ro_query)
                                   3 compute influence + scores in Python (transparent)
                                   4 explanation: LLM (optional) or deterministic template
GraphStore ──► FalkorDB (graph "ecomind")
```
**Why scoring is in Python, not Cypher:** every number can be shown and explained; the graph supplies structure and weights.
**Why a graph:** the answer depends on chains (`low_awareness → poor_sorting → school_waste`) and shared root causes. Following variable-length paths and counting fan-out is natural in Cypher and awkward across flat tables or a text-only chatbot.
**LLM boundary:** the LLM never writes queries; it only rephrases facts already retrieved.
