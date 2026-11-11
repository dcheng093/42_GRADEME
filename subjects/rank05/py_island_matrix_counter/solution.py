def island_matrix_counter(matrix: list[list[str]]) -> int:
    if not matrix or not matrix[0]:
        return 0
    rows, cols = len(matrix), len(matrix[0])
    seen = set()
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if matrix[r][c] != "1" or (r, c) in seen:
                continue
            islands += 1
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                y, x = stack.pop()
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < rows and 0 <= nx < cols and matrix[ny][nx] == "1" and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
    return islands
