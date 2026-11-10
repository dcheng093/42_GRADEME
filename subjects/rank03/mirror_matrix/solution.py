def mirror_matrix(matrix: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in matrix]


res = mirror_matrix([
                               [1, 2, 3],
                               [4, 5, 6],
                               [7, 8, 9]
                             ])

print("[")
for i, row in enumerate(res):
    comma = "," if i < len(res) - 1 else ""
    print(f"  {row}{comma}")
print("]")
