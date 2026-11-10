def twoSum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        needed = target - num
        if needed in seen:
            return [seen[needed], i]
        seen[num] = i
    return []


print(twoSum([2, 7, 11, 15], 9))    # [0, 1]
print(twoSum([5, 5], 10))           # [0, 1]
