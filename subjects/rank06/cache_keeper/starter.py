class CacheKeeper:
    def __init__(self, capacity: int) -> None:
        pass

    def get(self, key: int) -> int:
        raise NotImplementedError

    def put(self, key: int, value: int) -> None:
        pass
