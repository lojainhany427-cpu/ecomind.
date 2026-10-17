import unittest
from ecomind.engine import (Engine, InvalidRequest, normalize_weights, cause_influence, resolve_problem)
from tests.fakes import FakeStore


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(FakeStore())

    def test_weights_normalised(self):
        w = normalize_weights({"impact": 1, "cost": 1, "ease": 1, "confidence": 1})
        self.assertAlmostEqual(sum(w.values()), 1.0)

    def test_bad_weights(self):
        for bad in ({"x": 1}, {"impact": -1}, {"impact": "a"}, {"impact": 0, "cost": 0, "ease": 0, "confidence": 0}):
            with self.assertRaises(InvalidRequest):
                normalize_weights(bad)

    def test_influence_multi_hop(self):
        rows = [dict(cause="a", weights=[0.5, 0.5]), dict(cause="a", weights=[0.2])]
        self.assertAlmostEqual(cause_influence(rows)["a"], 0.45)

    def test_routing(self):
        probs = [dict(id="school_waste", name="n", keywords=["waste"])]
        self.assertEqual(resolve_problem("How do we cut waste?", probs)["id"], "school_waste")
        self.assertIsNone(resolve_problem("Tell me about pizza", probs))

    def test_investigate_end_to_end(self):
        r = self.engine.investigate("How can our school reduce waste?")
        self.assertEqual(r["problem_id"], "school_waste")
        self.assertEqual(r["explanation_mode"], "deterministic-template")
        self.assertEqual([d["rank"] for d in r["ranked"]], list(range(1, len(r["ranked"]) + 1)))
        scores = [d["score"] for d in r["ranked"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertIn("synthetic", r["explanation"].lower())

    def test_missing_evidence_flagged(self):
        r = self.engine.investigate("reduce school waste")
        self.assertIn("Student awareness campaign", r["missing_evidence"])
        aw = next(d for d in r["ranked"] if d["id"] == "awareness_campaign")
        self.assertEqual(aw["components"]["confidence"], 0.0)

    def test_weights_change_ranking(self):
        cheap = self.engine.investigate("school waste", {"impact": 0, "cost": 100, "ease": 0, "confidence": 0})
        self.assertEqual(cheap["ranked"][0]["id"], "double_sided_printing")  # lowest cost

    def test_trace_lists_queries(self):
        r = self.engine.investigate("school waste")
        names = [t["query"] for t in r["query_trace"]]
        for n in ("causal_paths", "interventions", "evidence", "edges"):
            self.assertIn(n, names)

    def test_invalid_questions(self):
        for bad in ("", "   ", None, "x" * 501, "pizza"):
            with self.assertRaises(InvalidRequest):
                self.engine.investigate(bad)
