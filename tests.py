import os
import tig
import unittest
import utils
import shutil
import tempfile

class TestSuite:
    def test_round_trip_blob(self):
        blob = tig.GitBlob("what's up boss")
        sha = self.git._write_object(blob)
        obj = self.git._read_object(sha)
        self.assertEqual(obj.data, b"what's up boss")
        self.assertEqual(obj.fmt, "blob")

    def test_round_trip_commit(self):
        commit = tig.GitCommit("tree some tree\nauthor Alex Jeon\n\nsome message")
        sha = self.git._write_object(commit)
        obj = self.git._read_object(sha)
        self.assertEqual(obj.fmt, "commit")
        self.assertEqual(obj.data["tree"], ["some tree"])
        self.assertEqual(obj.data["author"], ["Alex Jeon"])
        self.assertEqual(obj.data[None], "some message")

    def test_round_trip_tree(self):
        tree = tig.GitTree()
        tree_node = utils.TreeNode("100001", "some_path.txt", "0000000000000000000000000000000000012345")
        tree.data = [tree_node]
        sha = self.git._write_object(tree)
        obj = self.git._read_object(sha)

        self.assertEqual(obj.fmt, "tree")
        self.assertEqual(obj.data, [tree_node])

    def test_create_direct_ref(self):
        blob = tig.GitBlob("hello world")
        sha = self.git._write_object(blob)
        self.git.create_ref("", "salutations", sha)
        returned_sha = self.git._resolve_reference(".git/refs", "salutations")
        self.assertEqual(returned_sha, sha)

    def test_create_indirect_ref(self):
        blob = tig.GitBlob("hello world")
        original_sha = self.git._write_object(blob)
        self.git.create_ref("", "salutations", original_sha)
        self.git.create_ref("anon", "salutation", "ref: refs/salutations")
        returned_sha = self.git._resolve_reference(".git/refs/anon", "salutation")
        self.assertEqual(returned_sha, original_sha)

    def test_create_simple_tag(self):
        blob = tig.GitBlob("hello world")
        original_sha = self.git._write_object(blob)
        self.git.create_tag("tags", "another_salutation", original_sha)
        returned_sha = self.git.db.get(".git/refs/tags/another_salutation").decode()
        self.assertEqual(original_sha, returned_sha)

    def test_create_heavy_tag(self):
        blob = tig.GitBlob("hello world") 
        original_sha = self.git._write_object(blob)
        self.git.create_ref("", "salutations", original_sha)
        self.git.create_tag("tags", "another_salutation", original_sha, create_tag_object=True)
        returned_sha = self.git.db.get(".git/refs/tags/another_salutation").decode()
        returned_tag_obj = self.git._read_object(returned_sha)
        self.assertEqual(returned_tag_obj.data["tag"], ["another_salutation"])
        self.assertEqual(returned_tag_obj.data["type"], ["commit"])
        self.assertEqual(returned_tag_obj.data["object"], [original_sha])
        self.assertEqual(returned_tag_obj.data[None], "Some tag object") 

    def test_checkout(self):
        salutation = tig.GitBlob("hello world")
        response = tig.GitBlob("whats up boss")
        salutation_sha = self.git._write_object(salutation)
        response_sha = self.git._write_object(response)

        tree = tig.GitTree()
        tree.data = [
            utils.TreeNode("040000", "salutation.txt", salutation_sha),
            utils.TreeNode("040000", "response.txt", response_sha),
        ]
        tree_sha = self.git._write_object(tree)


        tree_info = f"tree {tree_sha}".encode()
        author_info = f"author Alex Jeon".encode()
        committer_info = f"committer Alex Jeon".encode()
        message = "My first commit!".encode()

        commit = tig.GitCommit(tree_info + b"\n" + author_info + b"\n" + committer_info + b"\n\n" + message)
        commit_sha = self.git._write_object(commit)

        self.git.db.set("working_dir", None)
        self.git.checkout(commit_sha, "working_dir")

            
    def test_find_object_no_tag(self):
        blob = tig.GitBlob("hello world")
        sha = self.git._write_object(blob)
        abbreviation = sha[:6]
        found_obj_sha = self.git._find_object(abbreviation)
        found_obj = self.git._read_object(found_obj_sha)
        self.assertEqual(found_obj.fmt, "blob")
        self.assertEqual(found_obj.data, b"hello world")


    def test_find_object_recursive(self):
        blob = tig.GitBlob("hello world")
        original_sha = self.git._write_object(blob)
        self.git.create_tag("tags", "another_salutation", original_sha)
        found_obj_sha = self.git._find_object("another_salutation")
        found_obj = self.git._read_object(found_obj_sha)
        self.assertEqual(found_obj.fmt, "blob")
        self.assertEqual(found_obj.data, b"hello world")


    def test_find_commit(self):
        salutation = tig.GitBlob("hello world")
        response = tig.GitBlob("whats up boss")
        salutation_sha = self.git._write_object(salutation)
        response_sha = self.git._write_object(response)

        tree = tig.GitTree()
        tree.data = [
            utils.TreeNode("040000", "salutation.txt", salutation_sha),
            utils.TreeNode("040000", "response.txt", response_sha),
        ]
        tree_sha = self.git._write_object(tree)

        tree_info = f"tree {tree_sha}".encode()
        author_info = f"author Alex Jeon".encode()
        committer_info = f"committer Alex Jeon".encode()
        message = "My first commit!".encode()

        commit = tig.GitCommit(tree_info + b"\n" + author_info + b"\n" + committer_info + b"\n\n" + message)
        commit_sha = self.git._write_object(commit)
        found_sha = self.git._find_object(commit_sha)
        self.assertEqual(found_sha, tree_sha)
        

    def test_find_head(self):
        salutation = tig.GitBlob("hello world")
        response = tig.GitBlob("whats up boss")
        salutation_sha = self.git._write_object(salutation)
        response_sha = self.git._write_object(response)

        tree = tig.GitTree()
        tree.data = [
            utils.TreeNode("040000", "salutation.txt", salutation_sha),
            utils.TreeNode("040000", "response.txt", response_sha),
        ]
        tree_sha = self.git._write_object(tree)

        tree_info = f"tree {tree_sha}".encode()
        author_info = f"author Alex Jeon".encode()
        committer_info = f"committer Alex Jeon".encode()
        message = "My first commit!".encode()

        commit = tig.GitCommit(tree_info + b"\n" + author_info + b"\n" + committer_info + b"\n\n" + message)
        commit_sha = self.git._write_object(commit)
        self.git.db.set(".git/HEAD", commit_sha.encode())

        current_branch_sha = self.git._get_current_branch()
        found_object_sha = self.git._find_object(current_branch_sha)

        self.assertEqual(found_object_sha, tree_sha)

    def test_git_add(self):
        self.git.db.set("working_dir", None)
        self.git.db.set("working_dir/salutation.txt", "hello world", no_encoding=True) # bytes
        self.git.add(["working_dir/salutation.txt"])

        index = self.git._get_index()
        self.assertEqual(len(index.entries), 1)
        self.assertEqual(index.entries[0].name, "salutation.txt")


    def test_git_rm(self):
        self.git.db.set("working_dir", None)
        self.git.db.set("working_dir/salutation.txt", "hello world".encode())
        self.git.add(["working_dir/salutation.txt"])
        self.git.rm(["salutation.txt"])

        index = self.git._get_index()
        self.assertEqual(len(index.entries), 0)


class TestGitFile(TestSuite, unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        self.git = tig.Git(self.temp_dir, dbType="fs")
        self.git.init()
        print("\nTesting FileDatabase:", self._testMethodName)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

class TestGitJSON(TestSuite, unittest.TestCase):
    def setUp(self):
        self.git = tig.Git("/Users/hwjeon/Documents/PROJECTS/tig/tests/git_db.json")
        self.git.init()
        print("\nTesting JSONDatabase:", self._testMethodName)

    def tearDown(self):
        self.git.db.clear()
        self.git.init()