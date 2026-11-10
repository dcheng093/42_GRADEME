def capitalize_words(s: str) -> str:
    return " ".join(word.capitalize() for word in s.split(" "))


print(capitalize_words("hello world"))           # "Hello World"
print(capitalize_words("42 madrid exam"))        # "42 Madrid Exam"
print(capitalize_words("  multiple   spaces "))  # "  Multiple   Spaces "
print(capitalize_words("mixed CASE letters"))    # "Mixed Case Letters"
