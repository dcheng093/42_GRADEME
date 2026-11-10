def rotate_90(matrix: list[list[int]]) -> list[list[int]]:
    return [[matrix[len(matrix) - 1 - j][i] for j in range(len(matrix))] for i in range(len(matrix))]


def main() -> None:
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    print(rotate_90(matrix))


if __name__ == "__main__":
    main()
