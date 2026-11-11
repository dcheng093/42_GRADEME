class UnionFind:
    def __init__(self, n: int) -> None:
        pass

    def find(self, x: int) -> int:
        raise NotImplementedError

    def union(self, x: int, y: int) -> bool:
        raise NotImplementedError

    def connected(self, x: int, y: int) -> bool:
        raise NotImplementedError
