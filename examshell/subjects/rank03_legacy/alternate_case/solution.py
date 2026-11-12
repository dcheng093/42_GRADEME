def alternate_case(s: str) -> str:
    res, count = "", 0
    for char in s:
        if char.isalpha():
            if count % 2 == 0:
                res += char.upper()
            else:
                res += char.lower()
            count += 1
        else:
            res += char
    return res
