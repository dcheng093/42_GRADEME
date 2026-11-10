def shadow_merge(list1: list[int], list2: list[int]) -> list[int]:
    result = []
    first_index = 0
    second_index = 0

    while first_index < len(list1) and second_index < len(list2):
        if list1[first_index] <= list2[second_index]:
            result.append(list1[first_index])
            first_index += 1
        else:
            result.append(list2[second_index])
            second_index += 1

    result.extend(list1[first_index:])
    result.extend(list2[second_index:])
    return result