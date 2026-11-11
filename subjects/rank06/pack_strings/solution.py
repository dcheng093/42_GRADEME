def pack(strs: list[str]) -> str:
    # every string as <length>#<string>: the length says where it ends,
    # so the string itself may contain anything
    return "".join(f"{len(s)}#{s}" for s in strs)


def unpack(s: str) -> list[str]:
    result = []
    i = 0
    while i < len(s):
        sep = s.index("#", i)
        length = int(s[i:sep])
        result.append(s[sep + 1:sep + 1 + length])
        i = sep + 1 + length
    return result
