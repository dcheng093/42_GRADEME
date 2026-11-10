def valid_anagram(s: str, t: str) -> bool:
    return sorted(s) == sorted(t)


print(valid_anagram("racecar", "carrace"))  # True
print(valid_anagram("jar", "jam"))          # False
print(valid_anagram("listen", "silent"))    # True
print(valid_anagram("aabbcc", "abcabc"))    # True
print(valid_anagram("abc", "ab"))           # False
