from collections import Counter


def string_permutation_checker(s1: str, s2: str) -> bool:
    return Counter(s1) == Counter(s2)