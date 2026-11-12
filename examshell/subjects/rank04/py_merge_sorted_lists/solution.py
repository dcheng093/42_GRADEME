def _merge_two(a: list[int], b: list[int]) -> list[int]:
    merged = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            merged.append(a[i])
            i += 1
        else:
            merged.append(b[j])
            j += 1
    merged.extend(a[i:])
    merged.extend(b[j:])
    return merged


def merge_sorted_lists(lists: list[list[int]]) -> list[int]:
    # merge pairs of lists until one is left: O(N log k)
    pending = [list(values) for values in lists if values]
    if not pending:
        return []
    while len(pending) > 1:
        nxt = []
        for i in range(0, len(pending), 2):
            if i + 1 < len(pending):
                nxt.append(_merge_two(pending[i], pending[i + 1]))
            else:
                nxt.append(pending[i])
        pending = nxt
    return pending[0]
