from collections import Counter


def anagram(s1: str, s2: str) -> bool:
    first = Counter(s1.replace(" ", "").casefold())
    second = Counter(s2.replace(" ", "").casefold())
    return first == second
