import re
import base64
import zlib


def is_node_id(value):
    # Check if the value matches the pattern
    pattern = r"^![0-9A-Fa-f]{8}$"
    return bool(re.match(pattern, value))


def list_choices(my_list, search=None):
    choice = 0
    response = ""
    if len(my_list) > 0:
        for value, display in my_list:
            choice += 1
            if not search or search.lower() in display.lower():
                response += f"{choice}) {display}\n"
    else:
        response += "None\n"
    if not response:
        response = f"No matches for {search}\n\n"
    return response


def make_node_list(nodes, fmt="ils"):
    my_list = []
    for node in sorted(nodes):
        value = node
        longName = get_longName(node, nodes)
        shortName = get_shortName(node, nodes)
        # display = f"{node} {longName} ({shortName})"
        display = ""
        if "i" in fmt:
            display += node
            if "l" in fmt or "s" in fmt:
                display += " "
        if "l" in fmt:
            display += longName
            if "s" in fmt:
                display += " "
        if "s" in fmt:
            if "l" in fmt:
                display += f"({shortName})"
            else:
                display += f"{shortName}"
        item = (value, display)
        my_list.append(item)
    return my_list


def get_longName(node_id, node_list):
    fallback = f"Meshtastic_{node_id[-4:]}"
    node = node_list.get(node_id, None)
    if node and node.get("user", None):
        return node["user"].get("longName", fallback)
    else:
        return fallback


def get_shortName(node_id, node_list):
    fallback = node_id[-4:]
    node = node_list.get(node_id, None)
    if node and node.get("user", None):
        return node["user"].get("shortName", fallback)
    else:
        return fallback


def encode(plaintext: str, delimiter: str) -> str:
    """
    Compress and Base64 encode a plaintext string.
    Return the encoded string if it is smaller than
    the plaintext or if the plaintext contains the
    delimiter. Otherwise, return the plaintext.
    """
    log.debug(f"Original Size: {len(plaintext)} bytes")
    compressed = zlib.compress(plaintext.encode("utf-8"))
    log.debug(f"Compressed Size: {len(compressed)} bytes")
    encoded = base64.b64encode(compressed).decode("utf-8")
    log.debug(f"Base64-Encoded Size: {len(encoded)} bytes")
    if len(encoded) < len(plaintext) or delimiter in plaintext:
        return encoded
    else:
        return plaintext


def decode(string: str) -> str:
    """
    Attempt to decode and decompress a string.
    If the string is not encoded, return it as-is.
    """
    try:
        decoded = base64.b64decode(string)
        decompressed = zlib.decompress(decoded)
        return decompressed.decode("utf-8")
    except (base64.binascii.Error, zlib.error, UnicodeDecodeError):
        return string
