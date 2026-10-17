"""Investigation engine: question -> problem id -> whitelisted graph queries -> transparent scoring."""
from .queries import QUERIES
from .seed_data import SYNTHETIC_NOTICE

DEFAULT_WEIGHTS = {"impact": 0.45, "cost": 0.2, "ease": 0.15, "confidence": 0.2}


class InvalidRequest(ValueError):
    pass


def normalize_weights(weights: dict | None) -> dict:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        if set(weights) - set(DEFAULT_WEIGHTS):
            raise InvalidRequest(f"Weights may only contain {sorted(DEFAULT_WEIGHTS)}")
        for k, v in weights.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 or v > 100:
                raise InvalidRequest(f"Weight '{k}' must be a number between 0 and 100")
            w[k] = float(v)
    total = sum(w.values())
    if total <= 0:
        raise InvalidRequest("At least one weight must be greater than zero")
    return {k: v / total for k, v in w.items()}


def resolve_problem(question: str, problems: list[dict]) -> dict | None:
    """Deterministic keyword routing. The question is never used inside Cypher."""
    q = question.lower()
    best, best_hits = None, 0
    for p in problems:
        hits = sum(1 for kw in (p.get("keywords") or []) if kw in q)
        if hits > best_hits:
            best, best_hits = p, hits
    return best


def cause_influence(path_rows: list[dict]) -> dict:
    """Influence of each cause on the problem = sum over its causal chains of the product of edge weights (cap 1)."""
    infl: dict[str, float] = {}
    for r in path_rows:
        prod = 1.0
        for w in r["weights"]:
            prod *= float(w if w is not None else 1.0)
        infl[r["cause"]] = infl.get(r["cause"], 0.0) + prod
    return {k: min(1.0, v) for k, v in infl.items()}


def score_interventions(rows, evidence_rows, influence, weights):
    by_i: dict[str, dict] = {}
    for r in rows:
        d = by_i.setdefault(r["id"], dict(id=r["id"], name=r["name"], description=r["description"],
                                          cost=float(r["cost"]), effort=float(r["effort"]), targets=[]))
        d["targets"].append(dict(cause=r["cause"], effect=float(r["effect"]),
                                 influence=round(influence.get(r["cause"], 0.0), 4)))
    ev: dict[str, list] = {}
    for e in evidence_rows:
        ev.setdefault(e["intervention"], []).append(e)
    raw = {i: sum(t["effect"] * t["influence"] for t in d["targets"]) for i, d in by_i.items()}
    top = max(raw.values()) if raw and max(raw.values()) > 0 else 1.0
    out = []
    for i, d in by_i.items():
        confs = [float(e["confidence"]) for e in ev.get(i, [])]
        comp = dict(impact=raw[i] / top, cost=1 - d["cost"], ease=1 - d["effort"],
                    confidence=(sum(confs) / len(confs)) if confs else 0.0)
        score = sum(weights[k] * comp[k] for k in comp)
        d.update(components={k: round(v, 3) for k, v in comp.items()}, score=round(score, 4),
                 raw_impact=round(raw[i], 4), evidence=ev.get(i, []),
                 missing_evidence=not confs)
        out.append(d)
    out.sort(key=lambda x: (-x["score"], x["id"]))
    for n, d in enumerate(out, 1):
        d["rank"] = n
    return out


def chain_strings(path_rows, cause_id, names):
    return [" → ".join(names.get(x, x) for x in r["ids"]) for r in path_rows if r["cause"] == cause_id]


def template_explanation(problem, ranked, paths, names, fanout, weights):
    lines = [f"Problem investigated: {problem['name']}. ({SYNTHETIC_NOTICE})", ""]
    for d in ranked[:3]:
        t = max(d["targets"], key=lambda t: t["effect"] * t["influence"])
        chains = chain_strings(paths, t["cause"], names)
        lines.append(f"#{d['rank']} {d['name']} (score {d['score']}): it addresses "
                     f"'{names.get(t['cause'], t['cause'])}' (effect {t['effect']}, influence on the problem "
                     f"{t['influence']}). Graph chain: {chains[0] if chains else 'n/a'}.")
        if d["missing_evidence"]:
            lines.append("   ⚠ No Evidence node is linked to this intervention, so its confidence score is 0.")
    hubs = [f for f in fanout if f["fanout"] > 1]
    if hubs:
        lines.append("")
        lines.append("Systemic leverage: " + ", ".join(
            f"'{names.get(h['id'], h['id'])}' drives {h['fanout']} other causes" for h in hubs) + ".")
    lines.append("")
    lines.append("Scoring weights used: " + ", ".join(f"{k}={v:.2f}" for k, v in weights.items()) + ".")
    return "\n".join(lines)


class Engine:
    def __init__(self, store, llm=None):
        self.store, self.llm = store, llm

    def investigate(self, question: str, weights: dict | None = None) -> dict:
        if not isinstance(question, str) or not question.strip():
            raise InvalidRequest("Question must be a non-empty string")
        if len(question) > 500:
            raise InvalidRequest("Question must be at most 500 characters")
        w = normalize_weights(weights)
        trace = []

        def q(name, params=None):
            rows = self.store.run(name, params)
            trace.append(dict(query=name, cypher=QUERIES[name], params=params or {}, rows=len(rows)))
            return rows

        problems = q("problems")
        problem = resolve_problem(question, problems)
        if not problem:
            raise InvalidRequest("No matching problem in the graph. Known problems: "
                                 + ", ".join(p["name"] for p in problems))
        pid = problem["id"]
        paths = q("causal_paths", {"pid": pid})
        infl = cause_influence(paths)
        cand = q("interventions", {"pid": pid})
        ids = sorted({r["id"] for r in cand})
        evidence = q("evidence", {"ids": ids}) if ids else []
        fanout = q("driver_fanout")
        ranked = score_interventions(cand, evidence, infl, w)
        node_ids = {pid} | {x for r in paths for x in r["ids"]} | set(ids) | {e["id"] for e in evidence}
        nodes = q("node_details", {"ids": sorted(node_ids)})
        edges = q("edges", {"ids": sorted(node_ids)})
        names = {n["id"]: n["name"] or n["id"] for n in nodes}
        for n in nodes:  # evidence nodes store 'label' not 'name'
            if n["name"] is None:
                for e in evidence:
                    if e["id"] == n["id"]:
                        names[n["id"]] = e["label"]
        explanation = template_explanation(problem, ranked, paths, names, fanout, w)
        mode, note = "deterministic-template", "No LLM used: explanation is a fixed template filled from graph results."
        if self.llm:
            try:
                explanation = self.llm.narrate(explanation)
                mode, note = "llm", "LLM rewrote the template using only the retrieved facts; verify against the evidence panel."
            except Exception as e:
                note = f"LLM unavailable ({type(e).__name__}); fell back to deterministic template."
        return dict(problem=problem["name"], problem_id=pid, ranked=ranked, explanation=explanation,
                    explanation_mode=mode, explanation_note=note, query_trace=trace,
                    graph=dict(nodes=nodes, edges=edges), weights=w,
                    assumptions=[SYNTHETIC_NOTICE,
                                 "Influence = sum over causal chains of the product of edge weights (capped at 1).",
                                 "Score = weighted sum of impact, low cost, ease, and evidence confidence."],
                    missing_evidence=[d["name"] for d in ranked if d["missing_evidence"]])
