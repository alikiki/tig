from collections import OrderedDict, namedtuple

TreeNode = namedtuple("TreeNode", "mode path sha")

def kvlm_read(kvlm):
    if not kvlm: 
        return {}
    
    parsed_kvlm = OrderedDict()
    lines = [l for l in kvlm.split("\n") if l]
    split_lines = [l.split(" ", 1) for l in lines]
    try:
        key_to_add = ""
        for key, value in split_lines:
            if key:
                key_to_add = key
            parsed_kvlm[key_to_add] = parsed_kvlm.get(key_to_add, []) + [value]
    except Exception as e:
        raise Exception(f"Parsing error: {e}")
    
    return parsed_kvlm
        

def kvlm_write(kv):
    kv.update({k: [v] for k, v in kv.items() if not isinstance(v, list)})
    stringified = {k: "\n ".join(v) for k, v in kv.items()}
    stringified_list = [f"{k} {v}" for k, v in stringified.items()]
    return "\n".join(stringified_list) + "\n"

def read_tree_node(data, start=0):
    mode_sep_pos = data.find(b' ', start)
    if mode_sep_pos < 5:
        raise Exception(f"Mode must be longer than 5 bytes. Your mode is only {mode_sep_pos} long.")
    elif mode_sep_pos > 6:
        raise Exception(f"Mode must be shorter than 6 bytes. Your mode is only {mode_sep_pos} long.")
    
    _mode = data[start:mode_sep_pos]
    mode = b" " + _mode if mode_sep_pos == 5 else _mode

    path_sep_pos = data.find(b'\x00', mode_sep_pos)
    path = data[(mode_sep_pos + 1):path_sep_pos]

    sha_1_length = 20
    sha = format(int.from_bytes(data[(path_sep_pos + 1):(path_sep_pos + sha_1_length + 1)], "big"), "040x")

    end_of_node = path_sep_pos + sha_1_length + 1
    return end_of_node, TreeNode(mode, path, sha)

def read_tree(data):
    curr_pos = 0
    tree = []
    while curr_pos < len(data):
        new_pos, tree_node = read_tree_node(data, start=curr_pos)
        curr_pos = new_pos
        tree.append(tree_node)

    return tree

def _order_fn(node: TreeNode):
    if node.mode.startwith(b"10"):
        return node.path
    else:
        return node.path if not node.path.endswith("/") else node.path + "/"
    
def write_tree_node(node):
    mode_str = node.mode
    path_str = node.path.encode('utf-8')
    sha_str = int(node.sha, 16).to_bytes(20, byteorder="big")

    return mode_str + b" " + path_str + b'\x00' + sha_str
    
def write_tree(data):
    ordered_tree = data.sort(key=_order_fn)
    return b"".join(write_tree_node(node) for node in ordered_tree)
