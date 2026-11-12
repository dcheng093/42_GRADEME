def _push(heap: list[int], value: int) -> None:
    heap.append(value)
    i = len(heap) - 1
    while i and heap[(i - 1) // 2] > heap[i]:
        heap[i], heap[(i - 1) // 2] = heap[(i - 1) // 2], heap[i]
        i = (i - 1) // 2


def _pop(heap: list[int]) -> int:
    top = heap[0]
    last = heap.pop()
    if heap:
        heap[0] = last
        i = 0
        while True:
            small = i
            for child in (2 * i + 1, 2 * i + 2):
                if child < len(heap) and heap[child] < heap[small]:
                    small = child
            if small == i:
                break
            heap[i], heap[small] = heap[small], heap[i]
            i = small
    return top


def task_order(n: int, prereqs: list[list[int]]) -> list[int]:
    after: list[list[int]] = [[] for _ in range(n)]
    waiting = [0] * n  # unfinished prerequisites per task
    for task, before in prereqs:
        after[before].append(task)
        waiting[task] += 1
    ready: list[int] = []
    for task in range(n):
        if waiting[task] == 0:
            _push(ready, task)
    order = []
    while ready:
        task = _pop(ready)  # smallest index first
        order.append(task)
        for nxt in after[task]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                _push(ready, nxt)
    return order if len(order) == n else []
