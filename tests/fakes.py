"""TEST DOUBLE — NOT FalkorDB. Answers the same named queries from the seed data in plain Python,
so engine/API logic can be tested without a database. It proves nothing about Cypher correctness;
tests/test_falkordb_integration.py does that against a real server."""
from ecomind import seed_data as S
from ecomind.queries import validate


class FakeStore:
    def __init__(self):
        self.edges = [(a, b, "CONTRIBUTES_TO", w) for a, b, w in S.CONTRIBUTES_TO] + \
                     [(a, b, "DRIVES", w) for a, b, w in S.DRIVES]

    def _paths(self, pid):
        out = []
        # enumerate chains cause->...->problem of length 1..3
        def dfs(cur, ids, ws):
            if len(ws) >= 3:
                return
            for a, b, _, w in self.edges:
                if a == cur:
                    nids, nws = ids + [b], ws + [w]
                    if b == pid:
                        out.append(dict(cause=ids[0], ids=nids, weights=nws, hops=len(nws)))
                    else:
                        dfs(b, nids, nws)
        for c in S.CAUSES:
            dfs(c["id"], [c["id"]], [])
        return out

    def run(self, name, params=None):
        params = validate(name, params)
        if name == "problems":
            return [dict(id=p["id"], name=p["name"], keywords=p["keywords"]) for p in S.PROBLEMS]
        if name == "causal_paths":
            return self._paths(params["pid"])
        if name == "interventions":
            reach = {r["cause"] for r in self._paths(params["pid"])}
            iv = {i["id"]: i for i in S.INTERVENTIONS}
            return [dict(id=i, name=iv[i]["name"], description=iv[i]["description"], cost=iv[i]["cost"],
                         effort=iv[i]["effort"], cause=c, effect=e)
                    for i, c, e in S.ADDRESSES if c in reach]
        if name == "evidence":
            ev = {e["id"]: e for e in S.EVIDENCE}
            return [dict(intervention=i, id=e, label=ev[e]["label"], confidence=ev[e]["confidence"], synthetic=True)
                    for i, e in S.SUPPORTED_BY if i in params["ids"]]
        if name == "driver_fanout":
            cnt = {}
            for a, b, _ in S.DRIVES:
                cnt[a] = cnt.get(a, 0) + 1
            return [dict(id=k, fanout=v) for k, v in sorted(cnt.items(), key=lambda x: -x[1])]
        names = {}
        for lab, items in (("Problem", S.PROBLEMS), ("Cause", S.CAUSES), ("Intervention", S.INTERVENTIONS), ("Evidence", S.EVIDENCE)):
            for x in items:
                names[x["id"]] = (lab, x.get("name"))
        if name == "node_details":
            return [dict(id=i, label=names[i][0], name=names[i][1]) for i in params["ids"] if i in names]
        if name == "edges":
            ids = set(params["ids"])
            e = [(a, t, b, w) for a, b, t, w in self.edges] + [(a, "ADDRESSES", b, w) for a, b, w in S.ADDRESSES] + \
                [(a, "SUPPORTED_BY", b, None) for a, b in S.SUPPORTED_BY]
            return [dict(src=a, rel=t, dst=b, w=w) for a, t, b, w in e if a in ids and b in ids]
        raise AssertionError(name)
