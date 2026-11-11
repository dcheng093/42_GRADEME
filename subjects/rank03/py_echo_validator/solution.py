def echo_validator(text: str) -> bool:
    letters = [char.casefold() for char in text if char.isalpha()]
    if not letters:
        return False
    return letters == letters[::-1]
