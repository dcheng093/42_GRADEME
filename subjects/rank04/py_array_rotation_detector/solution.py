def array_rotation_detector(arr1: list, arr2: list) -> bool:
    if len(arr1) != len(arr2):
        return False
    n = len(arr1)
    if n == 0:
        return True
    for shift in range(n):
        if all(arr1[(i + shift) % n] == arr2[i] for i in range(n)):
            return True
    return False
