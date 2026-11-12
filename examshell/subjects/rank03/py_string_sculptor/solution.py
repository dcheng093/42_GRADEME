def string_sculptor(text: str) -> str:
    result = []
    uppercase_next = False

    for char in text:
        if char.isalpha():
            result.append(char.upper() if uppercase_next else char.lower())
            uppercase_next = not uppercase_next
        else:
            result.append(char)

    return "".join(result)
