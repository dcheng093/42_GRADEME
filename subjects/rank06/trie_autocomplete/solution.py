def trie_autocomplete(words: list[str], prefix: str) -> list[str]:
    END = None  # key marking the end of a word (never a character)
    root = {}
    for word in words:
        node = root
        for char in word:
            node = node.setdefault(char, {})
        node[END] = True

    node = root
    for char in prefix:
        if char not in node:
            return []
        node = node[char]

    found = []
    stack = [(node, prefix)]
    while stack:
        node, word = stack.pop()
        if END in node:
            found.append(word)
        for char in node:
            if char is not END:
                stack.append((node[char], word + char))
    return sorted(found)
