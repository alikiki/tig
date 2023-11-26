import os
import gzip
import zlib
import hashlib
from collections import OrderedDict
from api.database import JsonDatabase

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

    def checkout(self, branch):
        pass

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
        pass

    def deserialize(self, data):
        pass
    
class GitTree(GitObject):
    def __init__(self, data):
        super().__init__(data)
        self.fmt = "tree"

    def serialize(self):
        pass

    def deserialize(self, data):
        pass

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


def kvlm_read(kvlm):
    parsed_kvlm = OrderedDict()

    start, pos = 0, 0
    while start < len(kvlm):
        spc = kvlm.find(b" ", start)
        newline = kvlm.find(b"\n", start)

        if (spc < 0) or (newline < spc):
            assert newline == start
            parsed_kvlm[None] = kvlm[(start+1):]
            return parsed_kvlm
    
        key = kvlm[start:spc]
        while kvlm[pos+1] != ord(' '):
            break

def kvlm_write(kvlm):
    pass


if __name__ == "__main__":
    homeDir = "/Users/hwjeon/Documents/PROJECTS/tig/tests/git_db.json"
    git = Git(homeDir)

    git.init()
    blob = GitBlob("hello world")
    git._write_object(blob)
