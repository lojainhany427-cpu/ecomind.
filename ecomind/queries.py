"""The ONLY Cypher the application can run: a fixed, named, parameterised whitelist.
User text never becomes Cypher; it is only mapped to a validated problem id."""
import re

ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")

QUERIES = {
    "problems": "MATCH (p:Problem) RETURN p.id AS id, p.name AS name, p.keywords AS keywords",
    # Multi-hop: every causal chain (1-3 hops) from a Cause to the Problem, with edge weights.
    "causal_paths": (
        "MATCH p=(c:Cause)-[:DRIVES|CONTRIBUTES_TO*1..3]->(pr:Problem {id:$pid}) "
        "RETURN c.id AS cause, [n IN nodes(p) | n.id] AS ids, "
        "[r IN relationships(p) | r.weight] AS weights, length(p) AS hops"),
    # Interventions that act on any cause that reaches the problem.
    "interventions": (
        "MATCH (i:Intervention)-[a:ADDRESSES]->(c:Cause) "
        "MATCH (c)-[:DRIVES|CONTRIBUTES_TO*1..3]->(:Problem {id:$pid}) "
        "RETURN DISTINCT i.id AS id, i.name AS name, i.description AS description, "
        "i.cost AS cost, i.effort AS effort, c.id AS cause, a.effect AS effect"),
    "evidence": (
        "MATCH (i:Intervention)-[:SUPPORTED_BY]->(e:Evidence) WHERE i.id IN $ids "
        "RETURN i.id AS intervention, e.id AS id, e.label AS label, "
        "e.confidence AS confidence, e.synthetic AS synthetic"),
    # Root causes that drive several other causes (systemic leverage points).
    "driver_fanout": (
        "MATCH (c:Cause)-[:DRIVES]->(d:Cause) RETURN c.id AS id, count(d) AS fanout "
        "ORDER BY fanout DESC"),
    "node_details": "MATCH (n) WHERE n.id IN $ids RETURN n.id AS id, labels(n)[0] AS label, n.name AS name",
    "edges": (
        "MATCH (a)-[r]->(b) WHERE a.id IN $ids AND b.id IN $ids "
        "RETURN a.id AS src, type(r) AS rel, b.id AS dst, coalesce(r.weight, r.effect) AS w"),
}

# param name -> kind
PARAM_SPEC = {
    "problems": {}, "causal_paths": {"pid": "id"}, "interventions": {"pid": "id"},
    "evidence": {"ids": "idlist"}, "driver_fanout": {}, "node_details": {"ids": "idlist"},
    "edges": {"ids": "idlist"},
}


class QueryError(ValueError):
    pass


def validate(name: str, params: dict | None) -> dict:
    params = params or {}
    if name not in QUERIES:
        raise QueryError(f"Unknown query '{name}'")
    spec = PARAM_SPEC[name]
    if set(params) != set(spec):
        raise QueryError(f"Query '{name}' expects parameters {sorted(spec)}")
    for k, kind in spec.items():
        v = params[k]
        if kind == "id" and not (isinstance(v, str) and ID_RE.match(v)):
            raise QueryError(f"Invalid id for '{k}'")
        if kind == "idlist":
            if not isinstance(v, list) or len(v) > 200 or not all(isinstance(x, str) and ID_RE.match(x) for x in v):
                raise QueryError(f"Invalid id list for '{k}'")
    return params
