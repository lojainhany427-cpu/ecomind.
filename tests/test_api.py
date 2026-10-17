import unittest
from ecomind.server import create_app
from tests.fakes import FakeStore


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.c = create_app(store=FakeStore()).test_client()

    def test_health(self):
        self.assertEqual(self.c.get("/api/health").status_code, 200)

    def test_investigate_ok(self):
        r = self.c.post("/api/investigate", json={"question": "How can the school reduce waste?"})
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertTrue(j["graph"]["nodes"] and j["graph"]["edges"] and j["query_trace"])

    def test_bad_requests(self):
        self.assertEqual(self.c.post("/api/investigate", data="nope").status_code, 400)
        self.assertEqual(self.c.post("/api/investigate", json={"question": "pizza"}).status_code, 400)
        self.assertEqual(self.c.post("/api/investigate", json={"question": "waste", "weights": {"impact": -5}}).status_code, 400)

    def test_no_raw_cypher_endpoint(self):
        self.assertEqual(self.c.post("/api/query", json={"cypher": "MATCH (n) RETURN n"}).status_code, 404)

    def test_index_served(self):
        self.assertEqual(self.c.get("/").status_code, 200)
