def palindrome_partitioner(s: str) -> int:
    n = len(s)
    if n <= 1:
        return 0
    # is_pal[i][j]: s[i..j] is a palindrome
    is_pal = [[False] * n for _ in range(n)]
    cuts = [0] * n  # cuts[j]: minimum cuts for s[0..j]
    for j in range(n):
        best = j
        for i in range(j + 1):
            if s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1]):
                is_pal[i][j] = True
                best = 0 if i == 0 else min(best, cuts[i - 1] + 1)
        cuts[j] = best
    return cuts[n - 1]
