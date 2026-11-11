class PrefixDictionary:
    def __init__(self):
        self.root = {}
        self.END = "$"  # marks the end of an inserted word (inputs are a-z only)

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            node = node.setdefault(char, {})
        node[self.END] = True

    def _walk(self, text):
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
