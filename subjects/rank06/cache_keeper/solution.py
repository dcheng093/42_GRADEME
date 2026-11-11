class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=0, value=0):
        self.key, self.value = key, value
        self.prev = self.next = None


class CacheKeeper:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.nodes = {}
        # sentinels: head.next is the most recent, tail.prev the least recent
        self.head, self.tail = _Node(), _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        node = self.nodes.get(key)
        if node is None:
            return -1
        self._unlink(node)
        self._push_front(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        node = self.nodes.get(key)
        if node is not None:
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return
        node = _Node(key, value)
        self.nodes[key] = node
        self._push_front(node)
        if len(self.nodes) > self.capacity:
            oldest = self.tail.prev
            self._unlink(oldest)
            del self.nodes[oldest.key]
