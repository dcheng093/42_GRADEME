def mirror_matrix_vertical(matrix: list) -> list:
    return matrix[::-1]


res = mirror_matrix_vertical([
                               [1, 2, 3],
                               [4, 5, 6],
                               [7, 8, 9]
                             ])

print("[")
for i, row in enumerate(res):
    comma = "," if i < len(res) - 1 else ""
    print(f"  {row}{comma}")
print("]")
