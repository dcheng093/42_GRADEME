def hidenp(small: str, big: str) -> bool:
    remaining = iter(big)
    return all(
        any(char == candidate for candidate in remaining) for char in small
    )
