def twist_sequence(arr: list[int], k: int) -> list[int]:
    if not arr:
        return []

    shift = k % len(arr)
    if shift == 0:
        return arr[:]
    return arr[-shift:] + arr[:-shift]
