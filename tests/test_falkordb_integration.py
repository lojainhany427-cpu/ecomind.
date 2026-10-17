"""Runs ONLY when a real FalkorDB server is reachable (see README). Otherwise skipped."""
import unittest
from ecomind.config import load_config
from ecomind.db import GraphStore, DatabaseUnavailable
from ecomind.engine import Engine

try:
    STORE = GraphStore(load_config())
    STORE.seed(reset=True)
    ERR = None
except Exception as e:  # DatabaseUnavailable, ImportError, ...
    STORE, ERR = None, e


@unittest.skipIf(STORE is None, f"FalkorDB not available: {ERR}")
class TestRealFalkorDB(unittest.TestCase):
    def test_connectivity(self):
        self.assertTrue(STORE.ping())

    def test_graph_initialised(self):
        self.assertEqual(STORE.run("problems")[0]["id"], "school_waste")

    def test_multi_hop_paths(self):
        rows = STORE.run("causal_paths", {"pid": "school_waste"})
        self.assertTrue(any(r["hops"] == 2 and r["cause"] == "low_awareness" for r in rows))

    def test_interventions_and_evidence(self):
        ids = {r["id"] for r in STORE.run("interventions", {"pid": "school_waste"})}
        self.assertIn("sorting_stations", ids)
        ev = STORE.run("evidence", {"ids": ["sorting_stations"]})
        self.assertEqual(len(ev), 1)

    def test_full_workflow(self):
        r = Engine(STORE).investigate("How can our school reduce waste?")
        self.assertEqual(r["problem_id"], "school_waste")
        self.assertTrue(r["ranked"])


if __name__ == "__main__":
    unittest.main()
