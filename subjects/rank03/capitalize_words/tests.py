def run(module, check):
    cases = [
        # basic
        ("hello", "Hello"),
        ("world", "World"),
        ("hello world", "Hello World"),
        ("good morning", "Good Morning"),
        ("hello python", "Hello Python"),
        ("this is a test", "This Is A Test"),
        ("one two three", "One Two Three"),
        ("python programming language", "Python Programming Language"),
        ("capitalize every word", "Capitalize Every Word"),
        ("hello world today", "Hello World Today"),

        # mixed case
        ("HELLO", "Hello"),
        ("WORLD", "World"),
        ("hELLO", "Hello"),
        ("HeLLo", "Hello"),
        ("HELLo WoRLD", "Hello World"),
        ("mIXED case", "Mixed Case"),
        ("PyThOn PrOgRaMmInG", "Python Programming"),
        ("tEST case", "Test Case"),
        ("aBcDeF", "Abcdef"),
        ("ABC DEF GHI", "Abc Def Ghi"),

        # multiple spaces
        ("  hello", "  Hello"),
        ("hello  world", "Hello  World"),
        ("hello   world", "Hello   World"),
        ("hello    world", "Hello    World"),
        ("  hello world", "  Hello World"),
        ("hello world  ", "Hello World  "),
        ("  hello world  ", "  Hello World  "),
        ("  multiple   spaces ", "  Multiple   Spaces "),
        ("hello    beautiful    world", "Hello    Beautiful    World"),
        ("   hello   world   test   ", "   Hello   World   Test   "),

        # empty and spaces
        ("", ""),
        (" ", " "),
        ("  ", "  "),
        ("   ", "   "),
        ("    hello    ", "    Hello    "),
        ("\t", "\t"),
        ("\n", "\n"),

        # single-letter words
        ("a", "A"),
        ("i", "I"),
        ("a b", "A B"),
        ("a b c", "A B C"),
        ("x y z", "X Y Z"),
        ("A B C", "A B C"),
        ("i am here", "I Am Here"),
        ("a simple test", "A Simple Test"),
        ("x marks spot", "X Marks Spot"),
        ("i love python", "I Love Python"),

        # numbers
        ("42", "42"),
        ("123", "123"),
        ("42 madrid", "42 Madrid"),
        ("123 hello", "123 Hello"),
        ("hello 123", "Hello 123"),
        ("42 madrid exam", "42 Madrid Exam"),
        ("123 abc def", "123 Abc Def"),
        ("hello 42 world", "Hello 42 World"),
        ("1 2 3 hello", "1 2 3 Hello"),
        ("42 PYTHON 99 TEST", "42 Python 99 Test"),

        # numbers attached to letters
        ("abc123", "Abc123"),
        ("123abc", "123abc"),
        ("hello123", "Hello123"),
        ("123hello", "123hello"),
        ("abc123def", "Abc123def"),
        ("123abc456", "123abc456"),
        ("42madrid", "42madrid"),
        ("madrid42", "Madrid42"),
        ("test123case", "Test123case"),
        ("123test123", "123test123"),

        # punctuation
        ("hello!", "Hello!"),
        ("hello?", "Hello?"),
        ("hello.", "Hello."),
        ("hello,", "Hello,"),
        ("hello;", "Hello;"),
        ("hello:", "Hello:"),
        ("hello-world", "Hello-world"),
        ("hello_world", "Hello_world"),
        ("hello/world", "Hello/world"),
        ("hello@world", "Hello@world"),

        # punctuation between words
        ("hello, world", "Hello, World"),
        ("hello! world", "Hello! World"),
        ("hello? world", "Hello? World"),
        ("hello. world", "Hello. World"),
        ("hello; world", "Hello; World"),
        ("hello: world", "Hello: World"),
        ("hello - world", "Hello - World"),
        ("hello / world", "Hello / World"),
        ("hello @ world", "Hello @ World"),
        ("hello # world", "Hello # World"),

        # punctuation + multiple words
        ("hello,world", "Hello,world"),
        ("hello,world test", "Hello,world Test"),
        ("hello.world test", "Hello.world Test"),
        ("hello-world test", "Hello-world Test"),
        ("hello/world test", "Hello/world Test"),
        ("hello!world test", "Hello!world Test"),
        ("hello?world test", "Hello?world Test"),
        ("hello_world test", "Hello_world Test"),
        ("hello@world test", "Hello@world Test"),
        ("hello#world test", "Hello#world Test"),

        # longer sentences
        (
            "the quick brown fox",
            "The Quick Brown Fox",
        ),
        (
            "the QUICK BROWN fox jumps",
            "The Quick Brown Fox Jumps",
        ),
        (
            "this is a very long sentence",
            "This Is A Very Long Sentence",
        ),
        (
            "python is a great programming language",
            "Python Is A Great Programming Language",
        ),
        (
            "hello world this is python",
            "Hello World This Is Python",
        ),
        (
            "welcome to the world of programming",
            "Welcome To The World Of Programming",
        ),
        (
            "THE quick BROWN fox JUMPS over THE lazy DOG",
            "The Quick Brown Fox Jumps Over The Lazy Dog",
        ),
        (
            "  this   has    many spaces  ",
            "  This   Has    Many Spaces  ",
        ),
        (
            "42 madrid exam is tomorrow",
            "42 Madrid Exam Is Tomorrow",
        ),
        (
            "hello, world! this is a test.",
            "Hello, World! This Is A Test.",
        ),
    ]

    for value, expected in cases:
        result = module.capitalize_words(value)

        check(
            f"capitalize_words({value!r})",
            result,
            expected
        )
