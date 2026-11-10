def atoi(s: str) -> int:
    s, i, sign, res = s.strip(), 0, 1, 0
    if i < len(s) and s[i] in '+-':
        sign = -1 if s[i] == '-' else 1; i += 1
    while i < len(s) and s[i].isdigit():
        res = res * 10 + int(s[i]); i += 1
    return (sign * res)


print(atoi("42"))
print(atoi("  -42ab"))
print(atoi("+123"))
print(atoi("abc"))
