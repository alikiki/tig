import tig
import unittest
import utils

class TestGit(unittest.TestCase):
    def setUp(self):
        self.git = tig.Git("/Users/hwjeon/Documents/PROJECTS/tig/tests/git_db.json")
        self.git.init()

    def cleanUp(self):
        self.git.db.clear()
        self.git.init()

    def test_round_trip_blob(self):
        try:
            blob = tig.GitBlob("what's up boss")
            sha = self.git._write_object(blob)
            obj = self.git._read_object(sha)
            self.assertTrue(isinstance(obj.data, bytes))
            self.assertEqual(obj.data, b"what's up boss")
            self.assertEqual(obj.fmt, "blob")
        except Exception as e:
            self.cleanUp()
            raise Exception(e)
        
        self.cleanUp()

    def test_round_trip_commit(self):
        try:
            commit = tig.GitCommit("tree some tree\nauthor Alex Jeon\n\nsome message")
            sha = self.git._write_object(commit)
            obj = self.git._read_object(sha)
            self.assertEqual(obj.fmt, "commit")
            self.assertEqual(obj.data["tree"], ["some tree"])
            self.assertEqual(obj.data["author"], ["Alex Jeon"])
            self.assertEqual(obj.data[None], "some message")
        except Exception as e:
            self.cleanUp()
            raise Exception(e)
        
        self.cleanUp()

    def test_round_trip_tree(self):
        try:
            tree = tig.GitTree()
            tree_node = utils.TreeNode("100001", "some_path", "0000000000000000000000000000000000012345")
            tree.data = [tree_node]
            sha = self.git._write_object(tree)
            obj = self.git._read_object(sha)

            self.assertEqual(obj.fmt, "tree")
            self.assertEqual(obj.data, [tree_node])
        except Exception as e:
            self.cleanUp()
            raise Exception(e)
        
        self.cleanUp()

    def test_create_direct_ref(self):
        try:
            blob = tig.GitBlob("hello world")
            sha = self.git._write_object(blob)
            self.git.create_ref("", "salutations", sha)
            returned_sha = self.git._resolve_reference("/.git/refs", "salutations")
            self.assertEqual(returned_sha, sha)
        except Exception as e:
            self.cleanUp()
            raise Exception(e)
        
        self.cleanUp()

    def test_create_indirect_ref(self):
        try:
            blob = tig.GitBlob("hello world")
            original_sha = self.git._write_object(blob)
            self.git.create_ref("", "salutations", original_sha)
            self.git.create_ref("anon", "salutation", "ref: refs/salutations")
            returned_sha = self.git._resolve_reference("/.git/refs/anon", "salutation")
            self.assertEqual(returned_sha, original_sha)
        except Exception as e:
            self.cleanUp()
            raise Exception(e)
        
        self.cleanUp()

    def test_create_simple_tag(self):
        try:
            blob = tig.GitBlob("hello world")
            original_sha = self.git._write_object(blob)
            self.git.create_ref("", "salutations", original_sha)
            self.git.create_tag("tags", "another_salutation", "salutations")
            returned_sha = self.git.db.get("/.git/refs/tags/another_salutation").decode()
            self.assertEqual(original_sha, returned_sha)
        except Exception as e:
            self.cleanUp()
            raise Exception(e)
        
        self.cleanUp()    
