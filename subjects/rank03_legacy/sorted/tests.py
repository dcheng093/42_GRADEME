import random
from types import ModuleType
from typing import Any

from examshell.pytests import Check


def _expected(people: list[tuple[str, int]]) -> list[tuple[str, int]]:
    return sorted(people, key=lambda p: (p[1], p[0]))


def run(module: ModuleType, check: Check) -> None:
    cases: list[Any] = [
        [],
        [("Solo", 50)],
        [("B", 1), ("A", 1)],
        [("A", 2), ("B", 1)],
        [("Ana", 20), ("Luis", 20), ("Marta", 18)],
        [("bob", 30), ("Bob", 30), ("alice", 30), ("Alice", 30)],
        [("Same", 10), ("Same", 5), ("Same", 10)],
        [("Old", 99), ("Baby", 0), ("Mid", 45), ("Baby", 0)],
        [("Max", 21), ("Max", 12), ("Al", 21), ("Al", 12)],
        [("Z", 3), ("Y", 2), ("X", 1), ("W", 0)],
        [("Ab", 7), ("A", 7), ("Abc", 7), ("B", 7)],
    ]
    rng = random.Random(42)
    names = [
        "Ana",
        "Luis",
        "Marta",
        "Zoe",
        "Adam",
        "Eve",
        "Bob",
        "alice",
        "Lee",
        "Kim",
    ]
    for _ in range(60):
        size = rng.randint(2, 12)
        cases.append(
            [(rng.choice(names), rng.randint(0, 6)) for _ in range(size)]
        )

    for people in cases:
        original = list(people)
        expected = _expected(people)
        result = module.sort_people(people)
        errors = []
        if result != expected:
            errors.append(
                "\nwrong result\n"
                f"       Expected: {expected!r}\n"
                f"       Got:      {result!r}"
            )
        if people != original:
            errors.append(
                "\noriginal list was modified\n"
                f"       Original: {original!r}\n"
                f"       Got:      {people!r}"
            )
        if result is people and people:
            errors.append("\nfunction returned the original list object")
        check(f"sort_people({original!r})", not errors, True, errors)
