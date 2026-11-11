class PrefixDictionary:
    def __init__(self) -> None:
        pass

    def insert(self, word: str) -> None:
        pass

    def search(self, word: str) -> bool:
        raise NotImplementedError

    def starts_with(self, prefix: str) -> bool:
        raise NotImplementedError
