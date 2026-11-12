# def custom_sort(arr: list) -> list:
#     return sorted(arr)


def custom_sort(arr: list) -> list:
    res = arr[:]
    for i in range(len(res)):
        for j in range(len(res) - i - 1):
            if res[j] > res[j + 1]:
                res[j], res[j + 1] = res[j + 1], res[j]
    return res


print(custom_sort([3, 1, 2]))  # [1, 2, 3]
print(custom_sort([5, -1, 0]))  # [-1, 0, 5])
