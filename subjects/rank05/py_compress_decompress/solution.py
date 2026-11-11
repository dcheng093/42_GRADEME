def compress(s: str) -> str:
    parts = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        count = j - i
        parts.append(s[i] + (str(count) if count > 1 else ""))
        i = j
    return "".join(parts)


def decompress(s: str) -> str:
    parts = []
    i = 0
    while i < len(s):
        char = s[i]
        i += 1
        j = i
        while j < len(s) and "0" <= s[j] <= "9":
            j += 1
        parts.append(char * (int(s[i:j]) if j > i else 1))
        i = j
    return "".join(parts)
