from collections import OrderedDict, namedtuple

TreeNode = namedtuple("TreeNode", "mode path sha")

def kvlm_read(kvlm):
    if isinstance(kvlm, bytes):
        kvlm = kvlm.decode("utf-8")
    if not kvlm: 
        return {}
    
    parsed_kvlm = OrderedDict()
    lines = kvlm.split("\n")
    if not lines[0]:
        lines = lines[1:]
    if not lines[-1]:
        lines = lines[:-1]

    # iterate through until you hit an empty string
    split_lines = []
    line_num = 0
    while lines[line_num]:
        split_lines.append(lines[line_num].split(" ", 1))
        line_num += 1

    # add the kvlm information 
    try:
        key_to_add = ""
        for key, value in split_lines:
            if key:
                key_to_add = key
            parsed_kvlm[key_to_add] = parsed_kvlm.get(key_to_add, []) + [value]
    except Exception as e:
        raise Exception(f"Parsing error: {e}")

    # iterate through until you hit a non-empty string
    while not lines[line_num]:
        line_num += 1

    # this non-empty string is the message
    parsed_kvlm[None] = lines[line_num] 

    
    return parsed_kvlm
        

def kvlm_write(kv):
    named_fields = {k: v for k, v in kv.items() if k is not None}
    msg = kv[None]
    named_fields.update({k: [v] for k, v in named_fields.items() if not isinstance(v, list)})
    stringified = {k: "\n ".join(v) for k, v in named_fields.items()}
    stringified_list = [f"{k} {v}" for k, v in stringified.items()]
    stringified_kvlm = "\n".join(stringified_list) + "\n\n" + msg.strip()
    return stringified_kvlm.encode()

def read_tree_node(data, start=0):
    mode_sep_pos = data.find(b' ', start)
    if mode_sep_pos - start < 5:
        raise Exception(f"Mode must be longer than 5 bytes. Your mode is only {mode_sep_pos} bytes long.")
    elif mode_sep_pos - start > 6:
        raise Exception(f"Mode must be shorter than 6 bytes. Your mode is {mode_sep_pos} bytes long.")
    
    _mode = data[start:mode_sep_pos]
    mode = b" " + _mode if mode_sep_pos == 5 else _mode

    path_sep_pos = data.find(b'\x00', mode_sep_pos)
    path = data[(mode_sep_pos + 1):path_sep_pos]

    sha_1_length = 20
    sha = int.from_bytes(data[(path_sep_pos + 1):(path_sep_pos + sha_1_length + 1)], "big")

    end_of_node = path_sep_pos + sha_1_length + 1
    return end_of_node, TreeNode(mode.decode(), path.decode(), format(sha, "040x"))

def read_tree(data):
    curr_pos = 0
    tree = []

    while curr_pos < len(data):
        new_pos, tree_node = read_tree_node(data, start=curr_pos)
        curr_pos = new_pos
        tree.append(tree_node)

    return tree

def tree_order_fn(node: TreeNode):
    if node.mode.startswith("10"):
        return node.path
    else:
        return node.path if not node.path.endswith("/") else node.path + "/"
    
