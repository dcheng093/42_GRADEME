def cryptic_sorter(strings: list[str]) -> list[str]:
    vowels = "aeiou"

    def key(value: str) -> tuple[int, str, int]:
        lowered = value.casefold()
        vowel_count = sum(char in vowels for char in lowered)
        return len(value), lowered, vowel_count

    result = []
    for value in strings:
        index = len(result)
        value_key = key(value)
        while index > 0 and key(result[index - 1]) > value_key:
            index -= 1
        result.insert(index, value)
    return result