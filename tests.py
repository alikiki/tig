import connectors.database
import unittest

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.path = "/Users/hwjeon/Documents/PROJECTS/tig/tests/git_db.json"
        self.db = connectors.database.JsonDatabase(self.path)

    def test_get1(self):
        self.assertEqual(
            self.db.get("/"),
            {
                ".git": {
                    "object": "object",
                    "ref": "references"
                }
            })
        
    def test_get2(self):
        self.assertEqual(
            self.db.get("/.git"),
            {
                "object": "object",
                "ref": "references"
            })
        
    def test_get3(self):
        self.assertEqual(
            self.db.get("/.git/object"), "object")