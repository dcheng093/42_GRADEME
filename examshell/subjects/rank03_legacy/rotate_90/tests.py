from types import ModuleType
from typing import Any

from examshell.pytests import Check


def run(module: ModuleType, check: Check) -> None:

    cases: list[Any] = [
        # basic cases
        ([[1]], [[1]]),
        ([[1, 2], [3, 4]], [[3, 1], [4, 2]]),
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[7, 4, 1], [8, 5, 2], [9, 6, 3]]),
        # larger matrices
        (
            [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
            [[13, 9, 5, 1], [14, 10, 6, 2], [15, 11, 7, 3], [16, 12, 8, 4]],
        ),
        (
            [
                [1, 2, 3, 4, 5],
                [6, 7, 8, 9, 10],
                [11, 12, 13, 14, 15],
                [16, 17, 18, 19, 20],
                [21, 22, 23, 24, 25],
            ],
            [
                [21, 16, 11, 6, 1],
                [22, 17, 12, 7, 2],
                [23, 18, 13, 8, 3],
                [24, 19, 14, 9, 4],
                [25, 20, 15, 10, 5],
            ],
        ),
        # negative numbers
        ([[-1, -2], [-3, -4]], [[-3, -1], [-4, -2]]),
        (
            [[-1, -2, -3], [-4, -5, -6], [-7, -8, -9]],
            [[-7, -4, -1], [-8, -5, -2], [-9, -6, -3]],
        ),
        # zeros
        ([[0, 0], [0, 0]], [[0, 0], [0, 0]]),
        ([[0, 1], [2, 3]], [[2, 0], [3, 1]]),
        ([[0, 0, 1], [0, 2, 0], [3, 0, 0]], [[3, 0, 0], [0, 2, 0], [0, 0, 1]]),
        # duplicate values
        ([[1, 1], [1, 1]], [[1, 1], [1, 1]]),
        ([[1, 2], [2, 1]], [[2, 1], [1, 2]]),
        ([[1, 2, 1], [2, 3, 2], [1, 2, 1]], [[1, 2, 1], [2, 3, 2], [1, 2, 1]]),
        # negative and positive values
        ([[-1, 0], [0, 1]], [[0, -1], [1, 0]]),
        (
            [[-3, -2, -1], [0, 1, 2], [3, 4, 5]],
            [[3, 0, -3], [4, 1, -2], [5, 2, -1]],
        ),
        # strings
        ([["a", "b"], ["c", "d"]], [["c", "a"], ["d", "b"]]),
        (
            [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]],
            [["g", "d", "a"], ["h", "e", "b"], ["i", "f", "c"]],
        ),
        # single row/column is not valid because input is assumed square
        # empty matrix
        ([], []),
        # special values
        ([[True]], [[True]]),
        ([[None]], [[None]]),
        ([[1, None], [None, 2]], [[None, 1], [2, None]]),
        # already rotationally symmetric
        ([[1, 2], [2, 1]], [[2, 1], [1, 2]]),
        ([[1, 2, 1], [2, 3, 2], [1, 2, 1]], [[1, 2, 1], [2, 3, 2], [1, 2, 1]]),
        # negative and zero mix
        (
            [[-5, 0, 5], [-4, 0, 4], [-3, 0, 3]],
            [[-3, -4, -5], [0, 0, 0], [3, 4, 5]],
        ),
        # sequential values with a different layout
        ([[9, 8, 7], [6, 5, 4], [3, 2, 1]], [[3, 6, 9], [2, 5, 8], [1, 4, 7]]),
        # repeated rows
        ([[1, 2, 3], [1, 2, 3], [1, 2, 3]], [[1, 1, 1], [2, 2, 2], [3, 3, 3]]),
        # repeated columns
        ([[1, 1, 1], [2, 2, 2], [3, 3, 3]], [[3, 2, 1], [3, 2, 1], [3, 2, 1]]),
    ]

    for value, expected in cases:
        original = [row.copy() for row in value]

        result = module.rotate_90(value)

        check(
            f"rotate_90({value!r})",
            (result, value),
            (expected, original),
        )
