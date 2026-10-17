# Schema
Nodes: `Problem{id,name,keywords}`, `Cause{id,name}`, `Intervention{id,name,cost,effort,description}`, `Evidence{id,label,confidence}` — all seeded with `synthetic=true`.
Edges: `(Cause)-[:CONTRIBUTES_TO{weight}]->(Problem)`, `(Cause)-[:DRIVES{weight}]->(Cause)`, `(Intervention)-[:ADDRESSES{effect}]->(Cause)`, `(Intervention)-[:SUPPORTED_BY]->(Evidence)`.
Node ids are unique across labels. `awareness_campaign` deliberately has no Evidence, to demonstrate missing-evidence flagging.

# Queries (see `ecomind/queries.py` for exact text; all parameterised, read-only)
| Name | Purpose |
|---|---|
| `problems` | list problems/keywords for routing |
| `causal_paths` | all 1–3 hop `DRIVES|CONTRIBUTES_TO` chains from causes to the problem, with edge weights (multi-hop traversal) |
| `interventions` | interventions that `ADDRESSES` any cause that reaches the problem |
| `evidence` | evidence nodes linked to candidate interventions |
| `driver_fanout` | root causes that drive several causes (systemic leverage) |
| `node_details`, `edges` | induced subgraph for the visualization |

Scoring: influence(cause) = Σ over chains of Π edge weights (cap 1); impact(i) = Σ effect × influence, normalised by the best candidate; score = w·[impact, 1−cost, 1−effort, mean evidence confidence].
**Caveat:** these Cypher strings have not been executed against a live FalkorDB by the code's author yet.
