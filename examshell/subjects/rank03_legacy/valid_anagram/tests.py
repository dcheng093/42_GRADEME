from types import ModuleType
from typing import Any

from examshell.pytests import Check


def run(module: ModuleType, check: Check) -> None:

    cases: list[Any] = [
        # basic cases
        ("racecar", "carrace", True),
        ("jar", "jam", False),
        ("", "", True),
        ("listen", "silent", True),
        ("aabbcc", "abcabc", True),
        ("abc", "ab", False),
        ("hello", "hello", True),
        ("hello", "olleh", True),
        ("world", "dlrow", True),
        ("python", "typhon", True),
        # short strings
        ("a", "a", True),
        ("a", "b", False),
        ("ab", "ba", True),
        ("ab", "aa", False),
        ("abc", "cba", True),
        ("abc", "cab", True),
        ("abc", "acb", True),
        ("abc", "abd", False),
        ("abcd", "dcba", True),
        ("abcd", "abce", False),
        # repeated letters
        ("aa", "aa", True),
        ("aa", "ab", False),
        ("aaa", "aaa", True),
        ("aaa", "aa", False),
        ("aab", "aba", True),
        ("aab", "abb", False),
        ("abb", "bba", True),
        ("abb", "baa", False),
        ("aabb", "bbaa", True),
        ("aabb", "abab", True),
        # longer common words
        ("evil", "vile", True),
        ("evil", "live", True),
        ("evil", "veil", True),
        ("dusty", "study", True),
        ("angel", "glean", True),
        ("angle", "glean", True),
        ("below", "elbow", True),
        ("night", "thing", True),
        ("state", "taste", True),
        ("save", "vase", True),
        # common false anagrams
        ("evil", "vilex", False),
        ("dusty", "studyx", False),
        ("angel", "gleanx", False),
        ("below", "elbows", False),
        ("night", "thingy", False),
        ("state", "tastee", False),
        ("save", "vases", False),
        ("listen", "listens", False),
        ("triangle", "integralx", False),
        ("binary", "brainy", True),
        # longer true anagrams
        ("triangle", "integral", True),
        ("integral", "altering", True),
        ("conversation", "conservation", True),
        ("earth", "heart", True),
        ("heart", "earth", True),
        ("cheaters", "teachers", True),
        ("cheaters", "hectares", True),
        ("schoolmaster", "theclassroom", True),
        ("theeyes", "theysee", True),
        ("astronomer", "moonstarer", True),
        # duplicates and counts
        ("aaaab", "aabaa", True),
        ("aaaab", "aaaba", True),
        ("aaaab", "abaaa", True),
        ("aaaab", "abaaa", True),
        ("aabbbaa", "baaabba", True),
        ("aabbbaa", "abababa", True),
        ("aabbccdd", "ddccbbaa", True),
        ("aabbccdd", "abcdabcd", True),
        ("aaaabbbb", "bbaaaabb", True),
        ("aabcc", "ccaba", True),
        # false due to one count differing
        ("aabbcc", "aabbcd", False),
        ("aabbcc", "aabccc", False),
        ("aabbcc", "abbccc", False),
        ("aaabbb", "aabbbb", False),
        ("aaabbb", "aaaabb", False),
        ("abcd", "abcdd", False),
        ("abcd", "abcc", False),
        ("aabb", "aaab", False),
        ("aabbcc", "aabbc", False),
        ("abcabc", "abcabd", False),
        # numbers
        ("123", "321", True),
        ("12345", "54321", True),
        ("112233", "332211", True),
        ("112233", "123123", True),
        ("123123", "321321", True),
        ("1001", "0110", True),
        ("1001", "1010", True),
        ("112358", "835211", True),
        ("1234567890", "0987654321", True),
        ("1234", "1245", False),
        # letters and numbers
        ("a1b2", "2b1a", True),
        ("abc123", "321cba", True),
        ("a1a2", "2aa1", True),
        ("a1b1", "1ab1", True),
        ("a1b2c3", "3c2b1a", True),
        ("a1b2", "a1b3", False),
        ("abc123", "abc124", False),
        ("aabb11", "11bbaa", True),
        ("1122aa", "aa2211", True),
        ("123abc", "abc124", False),
    ]

    for first, second, expected in cases:
        result = module.valid_anagram(first, second)
        check(
            f"valid_anagram({first!r}, {second!r})",
            result,
            expected,
        )
