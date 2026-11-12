from collections import deque


def word_ladder(start: str, end: str, sentence: list[str]) -> int:
    words = set(sentence)
    if end not in words:
        return 0
    queue = deque([(start, 1)])
    seen = {start}
    letters = {c for w in words for c in w}
    while queue:
        word, length = queue.popleft()
        if word == end:
            return length
        for i in range(len(word)):
            for c in letters:
                if c == word[i]:
                    continue
                nxt = word[:i] + c + word[i + 1:]
                if nxt in words and nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, length + 1))
    return 0
