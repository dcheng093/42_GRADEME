def pattern_tracker(text: str) -> int:
    count = 0
    for i in range(len(text) - 1):
        if (text[i].isdigit() and
                text[i + 1].isdigit() and
                int(text[i + 1]) == int(text[i]) + 1):
            count += 1
    return count


print(pattern_tracker("12a34"))   # 2
print(pattern_tracker("1234"))    # 3
print(pattern_tracker("a1b2c3"))  # 0
print(pattern_tracker("98"))      # 0
