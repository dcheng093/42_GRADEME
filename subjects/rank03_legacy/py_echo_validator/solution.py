def py_echo_validator(s: str) -> bool:
    filtered = "".join(word.lower() for word in s if word.isalnum())
    return filtered[::-1] == filtered


print(py_echo_validator("Was it a car or a cat I saw?"))    # True
print(py_echo_validator("tab a cat"))                       # False
print(py_echo_validator("A man, a plan, a canal: Panama"))  # True
print(py_echo_validator("No lemon, no melon"))              # True
