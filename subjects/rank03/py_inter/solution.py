def inter(s1: str, s2: str) -> str:
    second = set(s2)
    seen = set()
    result = []

    for char in s1:
        if char in second and char not in seen:
            seen.add(char)
            result.append(char)

    return "".join(result)