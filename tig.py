import math
import re
import os
import hashlib
from utils import kvlm_read, kvlm_write, read_tree, tree_order_fn
from connectors.database import JsonDatabase

"""
b"" means that the string is stored as a sequence of bytes. 
"" means that the string is stored as a sequence of Unicode code points. 
"""

class Git():
    """
    Anything that deals with anything external should deal with BYTES.
    """
    def __init__(self, homeDir):
        self.db = JsonDatabase(homeDir)

        # BYTES because converts external -> internal rep
        self.obj_mapping = {
            b"commit": GitCommit,
            b"tree": GitTree,
            b"tag": GitTag,
            b"blob": GitBlob
        }

        # BYTES because converts external -> internal rep
        self.mode_mapping = {
            b"04": "tree",
            b"10": "blob",
            b"12": "blob",
            b"16": "commit"
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

    def rm(self):
        pass

    def ls_tree(self, ref, recursive=False, prefix_path=""):
        sha = self._resolve_reference("/.git/refs", ref)
        tree_obj = self._read_object(sha)

        for node in tree_obj.data:
            mode, path, sha = node
            obj_type = self.mode_mapping[mode[:2]]
            print(f"{mode} {obj_type} {sha} {os.path.join(prefix_path, path)}")

            if recursive and obj_type == "tree":
                self.ls_tree(sha, recursive=recursive, prefix_path=path)




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
        if (not isinstance(working_dir, dict)) or (working_dir):
            raise Exception(f"The working directory located at {working_dir_path} is not empty.")
        
        tree_obj = self._read_object(commit_obj.data["tree"][0])
        traversal_queue = []
        traversal_queue.extend(tree_obj.data)

        # needs to be DFS, otherwise there might not be a folder to add to
        while traversal_queue:
            curr_node = traversal_queue.pop()
            obj = self._read_object(curr_node.sha)
            dest = os.path.join(working_dir_path, curr_node.path)

            if obj.fmt == "tree":
                self.db.set(dest, None)
                traversal_queue.extend(obj.data)
            else:
                self.db.set(dest, obj.data.decode(), no_encoding=True)

    def create_ref(self, path, name, sha):
        self.db.set(os.path.join("/.git/refs", path), None)
        self.db.set(os.path.join("/.git/refs", path, name), sha.encode())

    def create_tag(self, path, name, ref, create_tag_object=False):
        obj_sha = self._find_object(ref)
        if create_tag_object:
            tag_obj = GitTag()
            tag_obj.data = {
                "tag": name,
                "type": "commit",
                "object": obj_sha,
                None: "Some tag object"
            }
            tag_obj_sha = self._write_object(tag_obj)
            self.create_ref(path, name, tag_obj_sha)
        else:
            self.create_ref(path, name, obj_sha)

    def create_branch(self, name):
        self.create_tag("heads", name, "main", create_tag_object=False)


    def show_ref(self):
        ref_data = {}
        self._get_all_references("/.git/refs", ref_data)
        for ref, sha in ref_data.items():
            print(f"{sha} {ref}")


    def _find_hashes(self, name):
        if not name:
            return []
        
        candidates = [] # accumulate object hashes
        hash_regex = re.compile(r"^[0-9A-Fa-f]{4,40}$")
        if hash_regex.match(name):
            head = name[:2]
            tail = name[2:]
            obj_candidates = self.db.get(f"/.git/objects/{head}")
            for t in obj_candidates.keys():
                if t.startswith(tail):
                    candidates.append(head + t)
        else:
            try:
                tag_candidate = self._resolve_reference("/.git/refs/tags", name)
                if tag_candidate:
                    candidates.append(tag_candidate)

                commit_candidate = self._resolve_reference("/.git/refs/heads", name)
                if commit_candidate:
                    candidates.append(commit_candidate)
            except:
                pass

        return candidates

    def _find_object(self, name, fmt=None):
        hashes = self._find_hashes(name)
        if not hashes:
            raise Exception(f"No hashes associated to {name} were found")
        if len(hashes) > 1:
            raise Exception(f"{name} refers to multiple hashes: {hashes}")
        
        found_hash = hashes[0]
        found_object = self._read_object(found_hash)
        if found_object.fmt == "tag":
            return found_object.data["object"][0]
        if found_object.fmt == "commit":
            return found_object.data["tree"][0]
        if (fmt is None) or (found_object.fmt == fmt):
            return found_hash
        


    def _read_object(self, sha):
        try:
            data = self.db.get(f"/.git/objects/{sha[:2]}/{sha[2:]}")
        except Exception as e:
            raise Exception(f"Object {sha} not found in database.")
    
        fmt_sep = data.find(b" ")
        fmt = data[:fmt_sep] # BYTES

        size_sep = data.find(b"\x00", fmt_sep)
        size = int(data[fmt_sep:size_sep].decode("ascii"))

        return self.obj_mapping[fmt](data[size_sep+1:])

    def _write_object(self, obj):
        # encoding from UNICODE --> BYTES
        fmt = obj.fmt.encode()
        content = obj.serialize()
        size = str(len(content)).encode()

        data_bytes = fmt + b' ' + size + b'\x00' + content

        sha = hashlib.sha1(data_bytes).hexdigest()

        self.db.set(f"/.git/objects/{sha[:2]}/", None)
        self.db.set(f"/.git/objects/{sha[:2]}/{sha[2:]}", data_bytes)

        return sha

    def _resolve_reference(self, path, ref):
        ref_path = os.path.join(path, ref)
        if self.db.is_folder(ref_path):
            return None
        
        data = self.db.get(ref_path).strip().decode()
        if data.startswith("ref: "):
            return self._resolve_reference("/.git", data[5:])
        else:
            return data
        
    def _get_all_references(self, path, acc):
        refs = self.db.get(path)
        for ref in refs:
            ref_path = os.path.join(path, ref)
            if self.db.is_folder(ref_path):
                self._get_all_references(ref_path, acc=acc)
            else:
                acc[ref_path] = self._resolve_reference(path, ref)



class GitObject():
    def __init__(self, data=None):
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
    def __init__(self, data=None):
        super().__init__(data)
        self.fmt = "commit"

    def serialize(self):
        return kvlm_write(self.data)

    def deserialize(self, data):
        if data is None:
            return {}
        return kvlm_read(data)
    
class GitTree(GitObject):
    def __init__(self, data=None):
        super().__init__(data)
        self.fmt = "tree"

    def serialize(self):
        ordered_tree = sorted(self.data, key=tree_order_fn)
        flattened_tree = []
        for node in ordered_tree:
            mode_str = node.mode.encode()
            path_str = node.path.encode()
            sha_str = int(node.sha, 16).to_bytes(20, byteorder="big")
            byte_str = mode_str + b' ' + path_str + b'\x00' + sha_str
            flattened_tree.append(byte_str)

        return b"".join(flattened_tree)


    def deserialize(self, data):
        if data is None:
            return []
        return read_tree(data)

class GitTag(GitCommit):
    def __init__(self, data=None):
        super().__init__(data)
        self.fmt = "tag"

class GitBlob(GitObject):
    def __init__(self, data):
        super().__init__(data)
        self.fmt = "blob"

    def serialize(self):
        return self.data.encode()

    def deserialize(self, data):
        return data

class GitIndexEntry():
    """
    HEADER (12 bytes):
        SIGNATURE (4 bytes): "DIRC" in ASCII
        VERSION (4 bytes): enum(2, 3, 4)
        NUMBER OF INDEX ENTRIES (4 bytes)

    SORTED INDEX ENTRIES

    EXTENSIONS

    HASH CHECKSUM
    """
    def __init__(self, 
                 ctime=None, mtime=None, dev=None, ino=None, mode_type=None, 
                 mode_perms=None, uid=None, gid=None, fsize=None, sha=None, 
                 flag_assume_valid=None, flag_stage=None, name=None):
        self.ctime = ctime
        self.mtime = mtime
        self.dev = dev 
        self.ino = ino
        self.mode_type = mode_type
        self.mode_perms = mode_perms
        self.uid = uid
        self.gid = gid
        self.fsize = fsize
        self.sha = sha
        self.flag_assume_valid = flag_assume_valid
        self.flag_stage = flag_stage
        self.name = name

class GitIndex():
    def __init__(self, entries=[]):
        self.entries = entries

    def read(self, data):
        if not isinstance(data, bytes):
            raise Exception("index data must be in bytes")
        
        curr_pos = 0

        header = data[(curr_pos):(curr_pos + 12)]
        curr_pos += 12

        signature = header[:4]
        version = header[4:8]
        num_index_entries = int(header[8:])

        if signature != b"DIRC":
            raise Exception(f"Signature must be \"DIRC\". Instead, it's {signature.decode()}")
        if version != b"2":
            raise Exception(f"tig only supports version 2. This is an index file of version {version.decode()}")
        

        entries = []
        for _ in range(num_index_entries):
            ctime_s = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            ctime_ns = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            mtime_s = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            mtime_ns = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            dev = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            ino = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            unused_space = int.from_bytes(data[(curr_pos):(curr_pos + 2)], "big")
            curr_pos += 2

            if unused_space != 0:
                raise Exception(f"In the \"mode\" section, the unused bits are not equal to zero; it's equal to {unused_space}")
            
            mode = int.from_bytes(data[(curr_pos):(curr_pos + 2)], "big") # total: 16 bits = 2 bytes
            curr_pos += 2

            mode_type = mode >> 12 # get the first 4 bits
            if mode_type not in [0b1000, 0b1010, 0b1110]:
                raise Exception(f"The mode type of this index entry must be '0b1000', '0b1010', or '0b1110'. The given mode type is {bin(mode_type)}")
            mode_perms = mode & 0b0000000111111111

            uid = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            gid = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            size = int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big")
            curr_pos += 4

            sha = format(int.from_bytes(data[(curr_pos):(curr_pos + 4)], "big"), "040x")
            curr_pos += 4

            flags = int.from_bytes(data[(curr_pos):(curr_pos + 2)], "big")
            curr_pos += 2

            flag_assume_valid = (flags & 0b1000000000000000) != 0 # get the first bit
            flag_extended = (flags & 0b0100000000000000) != 0 # get the second bit
            if flag_extended:
                raise Exception(f"In version 2, the 'extended' flag must be false.")
            flag_stage = (flags & 0b0011000000000000) # get the third and fourth bits
            flag_name_length = (flags & 0b0000111111111111) # get the last 12 bits

            if flag_name_length < 0xFFF:
                if data[(curr_pos + flag_name_length)] != 0x00: # entry path name should be null terminated
                    raise Exception("The last byte of the entry path name must be null.")
                entry_path_name = data[(curr_pos):(curr_pos + flag_name_length)]
                curr_pos += flag_name_length + 1 # 1 extra byte to account for the null terminator at pos `curr_pos + flag_name_length`
            else:
                null_pos = data.find(b"\x00", curr_pos + 0xFFF)
                entry_path_name = data[(curr_pos):(null_pos)]
                curr_pos = null_pos + 1 # 1 extra byte to account for the null terminator

            name = entry_path_name.decode("utf8")
            step_through_offset = 8 * math.ceil(curr_pos / 8) # however many bytes to skip to get to the next multiple of 8 bytes

            curr_pos += step_through_offset

            index_entry = GitIndexEntry(
                ctime = (ctime_s, ctime_ns),
                mtime = (mtime_s, mtime_ns),
                dev = dev,
                ino = ino,
                mode_type = mode_type,
                mode_perms = mode_perms,
                uid = uid,
                gid = gid,
                fsize = size,
                sha = sha,
                flag_assume_valid = flag_assume_valid,
                flag_stage = flag_stage,
                name = name
            )
            entries.append(index_entry)

        self.entries = entries