from typing import Any

# a trie node: child nodes by character, plus END -> True for a whole word
Node = dict[str, Any]


class PrefixDictionary:
    def __init__(self) -> None:
        self.root: Node = {}
        # marks the end of an inserted word (inputs are a-z only)
        self.END = "$"

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            node = node.setdefault(char, {})
        node[self.END] = True

    def _walk(self, text: str) -> Node | None:
        node = self.root
        for char in text:
            if char not in node:
                return None
            node = node[char]
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and self.END in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None
