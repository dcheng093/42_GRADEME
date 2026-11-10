def number_base_converter(number: str, from_base: int, to_base: int) -> str:
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if not 2 <= from_base <= 36 or not 2 <= to_base <= 36 or not number:
        return "ERROR"

    negative = number[0] == "-"
    start = 1 if number[0] in "+-" else 0
    if start == len(number):
        return "ERROR"

    value = 0
    for char in number[start:].upper():
        digit = digits.find(char)
        if digit < 0 or digit >= from_base:
            return "ERROR"
        value = value * from_base + digit

    if value == 0:
        return "0"

    converted = []
    while value:
        value, remainder = divmod(value, to_base)
        converted.append(digits[remainder])

    result = "".join(converted[::-1])
    return "-" + result if negative else result