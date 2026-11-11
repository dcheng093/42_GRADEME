def list_intersection_finder(lists: list[list[int]]) -> list[int]:
    if not lists:
        return []
    common = set(lists[0])
    for values in lists[1:]:
        common &= set(values)
    return sorted(common)
