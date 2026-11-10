def pattern_tracker(text: str) -> int:
    return sum(
        "0" <= first <= "8"
        and "0" <= second <= "9"
        and ord(second) == ord(first) + 1
        for first, second in zip(text, text[1:])
    )