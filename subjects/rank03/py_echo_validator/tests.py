def run(module, check):

    cases = [
        # basic palindromes
        ("", True),
        ("a", True),
        ("aa", True),
        ("aba", True),
        ("abba", True),
        ("abcba", True),
        ("racecar", True),
        ("level", True),
        ("radar", True),
        ("civic", True),

        # basic non-palindromes
        ("ab", False),
        ("abc", False),
        ("abcd", False),
        ("hello", False),
        ("world", False),
        ("python", False),
        ("palindrome", False),
        ("racecars", False),
        ("levelup", False),
        ("abcdef", False),

        # case-insensitive
        ("A", True),
        ("Aa", True),
        ("aA", True),
        ("AbA", True),
        ("ABCBA", True),
        ("RaceCar", True),
        ("RaCeCaR", True),
        ("LEVEL", True),
        ("LeVeL", True),
        ("CiViC", True),

        # case-insensitive non-palindromes
        ("Ab", False),
        ("aB", False),
        ("Abc", False),
        ("ABC", False),
        ("Racecars", False),
        ("Hello", False),
        ("Python", False),
        ("PyThOn", False),
        ("AbCd", False),
        ("WoRlD", False),

        # spaces
        ("a a", True),
        ("a b a", True),
        ("a b", False),
        ("race car", True),
        ("raceecar", True),
        ("never odd or even", True),
        ("never odd or even!", True),
        ("step on no pets", True),
        ("was it a car or a cat i saw", True),
        ("this is not a palindrome", False),

        # punctuation
        ("a!", True),
        ("!a!", True),
        ("a!b!a", True),
        ("a!b", False),
        ("a,b,a", True),
        ("a,b,c", False),
        ("madam!", True),
        ("madam?", True),
        ("madam.", True),
        ("hello!", False),

        # classic examples
        ("Was it a car or a cat I saw?", True),
        ("tab a cat", False),
        ("A man, a plan, a canal: Panama", True),
        ("No lemon, no melon", True),
        ("Never odd or even", True),
        ("Mr. Owl ate my metal worm", True),
        ("Do geese see God?", True),
        ("Was it Eliot's toilet I saw?", True),
        ("Yo, banana boy!", True),
        ("Eva, can I see bees in a cave?", True),

        # numbers
        ("1", True),
        ("11", True),
        ("12", False),
        ("121", True),
        ("12321", True),
        ("12345", False),
        ("1001", True),
        ("1002", False),
        ("1234321", True),
        ("1234567", False),

        # letters + numbers
        ("a1a", True),
        ("a1b", False),
        ("1a1", True),
        ("1ab1", False),
        ("1ab2", False),
        ("abc123cba", False),
        ("abc123", False),
        ("123abc321", False),
        ("123abc123", False),
        ("a1b2b1a", True),

        # special characters / symbols
        ("!!!", True),
        ("@@@", True),
        ("...", True),
        ("!@#$%", True),
        ("a!!!a", True),
        ("a!!!b", False),
        ("1!!!1", True),
        ("1!!!2", False),
        ("(())", True),
        ("(a)", True),

        # more mixed cases
        ("Madam, I'm Adam", True),
        ("Able was I ere I saw Elba", True),
        ("Taco cat", True),
        ("Taco cat!", True),
        ("A Toyota! Race fast, safe car! A Toyota!", True),
        ("Was it a rat I saw?", True),
        ("A Santa at NASA", True),
        ("Some men interpret nine memos", True),
        ("Too hot to hoot", True),
        ("Not a palindrome!", False),

        # whitespace-only / punctuation-only
        (" ", True),
        ("   ", True),
        ("\t", True),
        ("\n", True),
        ("!!!???", True),
        ("! ! !", True),
        ("  a  ", True),
        ("  abc  ", False),
        (" \t a \t ", True),
        (" \t abc \t ", False),
    ]

    for value, expected in cases:
        check(
            f"py_echo_validator({value!r})",
            module.py_echo_validator(value),
            expected
        )
