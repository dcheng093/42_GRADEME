
# sort strings by length
words = ["banana", "kiwi", "fig"]
result = sorted(words, key=lambda x: len(x))

print(result)

# sort tuples by a specific field
people = [("Ana", 8.5), ("Luis", 6.0)]
result = sorted(people, key=lambda x: x[1], reverse=True)

print(result)

# sort by multiple criteria
people = [("Ana", 20), ("Luis", 20), ("Marta", 18)]
result = sorted(people, key=lambda x: (x[1], x[0]))

print(result)
