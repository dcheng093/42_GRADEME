def convert_base(number: str, from_base: int, to_base: int) -> None:
    digits, res = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", ""
    try:
        if not (2 <= from_base <= 36 and 2 <= to_base <= 36):
            print("ERROR"); return
        digit = int(number, from_base)
    except ValueError:
        print("ERROR"); return
    if digit == 0:
        print("0"); return
    while digit > 0:
        res = res + digits[digit % to_base]; digit //= to_base
    print(res[::-1])


convert_base("ff", 16, 2)           # 11111111
convert_base("10", 2, 10)           # 2
convert_base("z", 36, 10)           # 35
convert_base("1g", 16, 10)          # ERROR
