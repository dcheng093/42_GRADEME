def brackets(s: str) -> bool:
    stack, pairs = [], {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in ')}]':
            if not stack or pairs[char] != stack[-1]:
                return False
            stack.pop()
    return len(stack) == 0


print(brackets("()"))               # True
print(brackets("([{}])"))           # True
print(brackets("(]"))               # False
print(brackets("([)"))              # False
print(brackets("a(b[c]d)"))         # True
print(brackets("[{adaudna}]"))      # True
print(brackets("[{adaudna}])"))     # False
print(brackets("abc{[123(xyz)]}"))  # True


# brackets("()")                    → True
# brackets("([{}])")                → True
# brackets("(]")                    → False
# brackets("([)")                   → False
# brackets("a(b[c]d)")              → True
# brackets("[{adaudna}]")           → True
# brackets("[{adaudna}])")          → False
# brackets("abc{[123(xyz)]}")       → True
