# function: parse_message reads structured text input (key: value format)
# and converts it into a Python dictionary.

def parse_message(raw: str) -> dict:
    """
    Parse key:value string into dictionary.
    Ignores lines without ':'.
    """
    result = {}
    try:
        for line in raw.strip().splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {e}")
        return {}
    return result

# function: serialize_message performs the reverse — it converts a dictionary
# into a text message with one key–value pair per line.

def serialize_message(msg: dict) -> str:
    """
    Convert dict to 'key: value' newline-separated string.
    """
    return '\n'.join(f"{k}: {v}" for k, v in msg.items())
