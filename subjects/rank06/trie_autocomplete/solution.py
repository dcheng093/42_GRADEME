from typing import Any


def trie_autocomplete(words: list[str], prefix: str) -> list[str]:
    END = None  # key marking the end of a word (never a character)
    # a node: child nodes by character, plus END -> True for a whole word
    root: dict[str | None, Any] = {}
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

    found: list[str] = []
    stack: list[tuple[dict[str | None, Any], str]] = [(node, prefix)]
    while stack:
        node, word = stack.pop()
        if END in node:
            found.append(word)
        for key in node:
            if key is not None:  # END
                stack.append((node[key], word + key))
    return sorted(found)
