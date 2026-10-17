"""Thin FalkorDB wrapper. Only whitelisted queries run, always read-only (ro_query)."""
from .config import Config
from .queries import QUERIES, validate
from . import seed_data


class DatabaseUnavailable(RuntimeError):
    pass


class GraphStore:
    def __init__(self, cfg: Config):
        try:
            from falkordb import FalkorDB
        except ImportError as e:  # pragma: no cover
            raise DatabaseUnavailable("Python package 'falkordb' is not installed (pip install -r requirements.txt)") from e
        self._cfg = cfg
        try:
            self._db = FalkorDB(host=cfg.host, port=cfg.port, username=cfg.username,
                                password=cfg.password, ssl=cfg.ssl)
            self._db.connection.ping()
        except Exception as e:
            raise DatabaseUnavailable(f"Cannot reach FalkorDB at {cfg.host}:{cfg.port} ({type(e).__name__})") from e
        self._graph = self._db.select_graph(cfg.graph)

    def ping(self) -> bool:
        return bool(self._db.connection.ping())

    def seed(self, reset: bool = True) -> int:
        """Create the synthetic school-waste graph. Returns number of statements run."""
        if reset:
            try:
                self._graph.delete()
            except Exception:
                pass  # graph did not exist yet
            self._graph = self._db.select_graph(self._cfg.graph)
        stmts = seed_data.seed_statements()
        for cypher, params in stmts:
            self._graph.query(cypher, params)
        return len(stmts)

    def ensure_seeded(self) -> bool:
        """Seed the synthetic graph only if it is missing/empty. Returns True if it seeded."""
        try:
            if self.run("problems"):
                return False
        except DatabaseUnavailable:
            pass  # graph does not exist yet
        self.seed(reset=False)
        return True

    def run(self, name: str, params: dict | None = None) -> list[dict]:
        params = validate(name, params)
        try:
            res = self._graph.ro_query(QUERIES[name], params)
        except Exception as e:
            raise DatabaseUnavailable(f"Query '{name}' failed: {e}") from e
        cols = [h[1] if isinstance(h, (list, tuple)) else h for h in res.header]
        return [dict(zip(cols, row)) for row in res.result_set]
