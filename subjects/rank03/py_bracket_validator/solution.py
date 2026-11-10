def bracket_validator(s: str) -> bool:
    pairs = {"(": ")", "[": "]", "{": "}"}
    closing = set(pairs.values())
    stack = []

    for char in s:
        if char in pairs:
            stack.append(char)
        elif char in closing:
            if not stack or pairs[stack.pop()] != char:
                return False

    return not stack