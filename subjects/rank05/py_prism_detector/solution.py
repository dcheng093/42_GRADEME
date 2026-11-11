DIRECTIONS = (
    ((1, 0), "H"), ((-1, 0), "H-"),
    ((0, 1), "V"), ((0, -1), "V-"),
    ((1, 1), "D1"), ((-1, -1), "D1-"),
    ((-1, 1), "D2"), ((1, -1), "D2-"),
)


def prism_detector(grid: list[str], pattern: str):
    if not grid or not pattern:
        return []
    found = []
    for y, row in enumerate(grid):
        for x in range(len(row)):
            for (dx, dy), code in DIRECTIONS:
                for i, char in enumerate(pattern):
                    cx, cy = x + dx * i, y + dy * i
                    if not (0 <= cy < len(grid) and 0 <= cx < len(grid[cy])) or grid[cy][cx] != char:
                        break
                else:
                    found.append((x, y, code))
    return found
