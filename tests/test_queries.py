import unittest
from ecomind.queries import validate, QueryError, QUERIES
from ecomind import seed_data


class TestValidation(unittest.TestCase):
    def test_unknown_query_rejected(self):
        with self.assertRaises(QueryError):
            validate("MATCH (n) DETACH DELETE n", {})

    def test_injection_in_id_rejected(self):
        with self.assertRaises(QueryError):
            validate("causal_paths", {"pid": "x'}) DETACH DELETE (n //"})

    def test_extra_params_rejected(self):
        with self.assertRaises(QueryError):
            validate("problems", {"pid": "school_waste"})

    def test_valid_params_ok(self):
        self.assertEqual(validate("causal_paths", {"pid": "school_waste"}), {"pid": "school_waste"})

    def test_all_queries_read_only(self):
        for name, cy in QUERIES.items():
            for bad in ("CREATE", "DELETE", "SET ", "MERGE", "REMOVE"):
                self.assertNotIn(bad, cy.upper(), name)

    def test_seed_is_parameterised_and_labelled_synthetic(self):
        for cy, params in seed_data.seed_statements():
            self.assertIn("$rows", cy)
        self.assertTrue(all(p["synthetic"] if "synthetic" in p else True for p in seed_data.PROBLEMS))
        self.assertIn("synthetic", seed_data.SYNTHETIC_NOTICE.lower())
