def sort_people(people: list[tuple[str, int]]) -> list[tuple[str, int]]:
    return sorted(people, key=lambda p: (p[1], p[0]))


print(sort_people([("Zoe", 30), ("Adam", 25)]))  # [('Adam', 25), ('Zoe', 30)]
print(sort_people([("Bob", 40), ("Alice", 40), ("Eve", 19)]))  # [('Eve', 19), ('Alice', 40), ('Bob', 40)]
