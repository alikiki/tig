import os
import gzip
import zlib
import hashlib
from utils import kvlm_read, kvlm_write, read_tree, write_tree
from connectors.database import JsonDatabase

class Git():
    def __init__(self, homeDir):
        self.db = JsonDatabase(homeDir)
        self.obj_mapping = {
            b"commit": GitCommit,
            b"tree": GitTree,
            b"tag": GitTag,
            b"blob": GitBlob
        }

    def init(self):
        self.db.set("/.git", None)
        self.db.set("/.git/objects", None)
        self.db.set("/.git/refs", None)
        self.db.set("/.git/refs/heads", None)
        self.db.set("/.git/refs/tags", None)
        self.db.set("/.git/objects/pack", None)

    def commit(self, msg):
        pass

    def add(self, paths):
        pass

    def checkout(self, commit, working_dir_path):
        """
        Updates working directory with information inside the commit

        commit: sha-1 hash
        working_dir: path to an EMPTY directory 
        """

        """
        COMMIT FORMAT:
        tree 29ff16c9c14e2652b22f8b78bb08a5a07930c147
        parent 206941306e8a8af65b66eaaaea388a7ae24d49a0
        author Thibault Polge <thibault@thb.lt> 1527025023 +0200
        committer Thibault Polge <thibault@thb.lt> 1527025044 +0200
        gpgsig ...some PGP signature...

        Create first draft
        """

        commit_obj = self._read_object(commit)
        if commit_obj.fmt != "commit":
            raise Exception(f"The chosen git object is not a commit; it is a {commit_obj.fmt}. Please choose a git object that is a commit.")
        
        working_dir = self.db.get(working_dir_path)
        if (not isinstance(working_dir, list)) or (not working_dir):
            raise Exception(f"The working directory located at {working_dir_path} is not empty.")
        
        tree_obj = commit_obj.data["tree"]
        traversal_queue = [tree_obj]

        # needs to be DFS, otherwise there might not be a folder to add to
        while traversal_queue:
            curr_node = traversal_queue.pop()
            obj = self._read_object(curr_node.sha)
            dest = os.path.join(working_dir_path, curr_node.path)

            if obj.fmt == "tree":
                self.db.set(dest, None)
                traversal_queue.extend(obj.data)
            else:
                self.db.set(dest, obj.data)

    def _read_object(self, sha):
        try:
            data = self.db.get(f"/.git/objects/{sha[:2]}/{sha[2:]}")
            data = self.db.deserialize_data(data)
        except Exception as e:
            raise Exception(f"Object {sha} not found in database.")
    
        fmt_sep = data.find(b" ")
        fmt = data[:fmt_sep]
        print(f"fmt: {fmt}")
        print(f"fmt sep: {fmt_sep}")

        size_sep = data.find(b"\x00", fmt_sep)
        size = int(data[fmt_sep:size_sep].decode("ascii"))
        print(f"size: {size}")
        print(f"size sep: {size_sep}")

        return self.obj_mapping[fmt](data[size_sep+1:])

    def _write_object(self, obj):
        fmt = obj.fmt.encode()
        content = obj.serialize().encode()
        size = str(len(content)).encode()

        data_bytes = fmt + b' ' + size + b'\x00' + content
        compressedData = self.db.serialize_data(data_bytes)

        sha = hashlib.sha1(data_bytes).hexdigest()

        self.db.set(f"/.git/objects/{sha[:2]}/", None)
        self.db.set(f"/.git/objects/{sha[:2]}/{sha[2:]}", compressedData)


class GitObject():
    def __init__(self, data):
        # FIXME
        # actually i don't like this because it doesn't make it explicit what is happening when you initialize the data
        # it might be annoying, but at least it's explicit when you call deserialize that you're setting self.data to something

        # like, why even have the deserialize be public if the user is never goign to call it anyway..? 
        self.data = self.deserialize(data)

    def serialize(self):
        raise Exception("Not implemented")

    def deserialize(self, data):
        raise Exception("Not implemented")


class GitCommit(GitObject):
    def __init__(self, data):
        super().__init__(data)
        self.fmt: str = "commit"

    def serialize(self):
        return kvlm_write(self.data)

    def deserialize(self, data):
        return kvlm_read(data)
    
class GitTree(GitObject):
    def __init__(self, data):
        super().__init__(data)
        self.fmt = "tree"

    def serialize(self):
        return write_tree(self.data)

    def deserialize(self, data):
        return read_tree(data)

class GitTag(GitObject):
    def __init__(self, data):
        super().__init__(data)
        self.fmt = "tag"

    def serialize(self):
        pass

    def deserialize(self, data):
        pass

class GitBlob(GitObject):
    def __init__(self, data):
        super().__init__(data)
        self.fmt = "blob"

    def serialize(self):
        return self.data

    def deserialize(self, data):
        return data


if __name__ == "__main__":
    homeDir = "/Users/hwjeon/Documents/PROJECTS/tig/tests/git_db.json"
    git = Git(homeDir)

    git.init()
    blob = GitBlob("hello world")
    git._write_object(blob)
