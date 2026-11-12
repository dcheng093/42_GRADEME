from types import ModuleType
from typing import Any

from examshell.pytests import Check


def run(module: ModuleType, check: Check) -> None:
    cases: list[Any] = [
        # basic words
        ("hello", "HeLlO"),
        ("world", "WoRlD"),
        ("python", "PyThOn"),
        ("testing", "TeStInG"),
        ("computer", "CoMpUtEr"),
        ("programming", "PrOgRaMmInG"),
        ("abcdef", "AbCdEf"),
        ("abcdefgh", "AbCdEfGh"),
        ("abcdefghi", "AbCdEfGhI"),
        ("abcdefghij", "AbCdEfGhIj"),
        # multiple words
        ("hello world", "HeLlO wOrLd"),
        ("hello python", "HeLlO pYtHoN"),
        ("good morning", "GoOd MoRnInG"),
        ("good night", "GoOd NiGhT"),
        ("test case", "TeSt CaSe"),
        ("alternate case", "AlTeRnAtE cAsE"),
        ("hello there friend", "HeLlO tHeRe FrIeNd"),
        ("this is a test", "ThIs Is A tEsT"),
        ("python is fun", "PyThOn Is FuN"),
        ("i love coding", "I lOvE cOdInG"),
        # empty and whitespace
        ("", ""),
        (" ", " "),
        ("  ", "  "),
        ("   ", "   "),
        ("hello ", "HeLlO "),
        (" hello", " HeLlO"),
        (" hello ", " HeLlO "),
        ("hello  world", "HeLlO  wOrLd"),
        ("hello   world", "HeLlO   wOrLd"),
        ("  hello  world  ", "  HeLlO  wOrLd  "),
        # lowercase input
        ("a", "A"),
        ("ab", "Ab"),
        ("abc", "AbC"),
        ("abcd", "AbCd"),
        ("abcde", "AbCdE"),
        ("abcdef", "AbCdEf"),
        ("abcdefgh", "AbCdEfGh"),
        ("aaaaaaaa", "AaAaAaAa"),
        ("bbbbbbbb", "BbBbBbBb"),
        ("helloworld", "HeLlOwOrLd"),
        # uppercase input
        ("A", "A"),
        ("AB", "Ab"),
        ("ABC", "AbC"),
        ("ABCD", "AbCd"),
        ("ABCDE", "AbCdE"),
        ("ABCDEF", "AbCdEf"),
        ("ABCDEFGH", "AbCdEfGh"),
        ("AAAAAAAA", "AaAaAaAa"),
        ("BBBBBBBB", "BbBbBbBb"),
        ("HELLOWORLD", "HeLlOwOrLd"),
        # mixed input case
        ("hElLo", "HeLlO"),
        ("HeLLo", "HeLlO"),
        ("HELlo", "HeLlO"),
        ("hELLO", "HeLlO"),
        ("PyThOn", "PyThOn"),
        ("PYTHON", "PyThOn"),
        ("python", "PyThOn"),
        ("pYtHoN", "PyThOn"),
        ("TeStInG", "TeStInG"),
        ("tEsTiNg", "TeStInG"),
        # numbers
        ("123", "123"),
        ("12345", "12345"),
        ("1hello", "1HeLlO"),
        ("2world", "2WoRlD"),
        ("42madrid", "42MaDrId"),
        ("123abc", "123AbC"),
        ("abc123", "AbC123"),
        ("1a2b3c", "1A2b3C"),
        ("hello123", "HeLlO123"),
        ("123hello", "123HeLlO"),
        # numbers between letters
        ("hello123world", "HeLlO123wOrLd"),
        ("abc123def", "AbC123dEf"),
        ("12hello34", "12HeLlO34"),
        ("test123case", "TeSt123CaSe"),
        ("123test456", "123TeSt456"),
        # punctuation
        ("hello!", "HeLlO!"),
        ("hello?", "HeLlO?"),
        ("hello.", "HeLlO."),
        ("hello,", "HeLlO,"),
        ("hello-world", "HeLlO-wOrLd"),
        ("hello_world", "HeLlO_wOrLd"),
        ("hello.world", "HeLlO.wOrLd"),
        ("hello/world", "HeLlO/wOrLd"),
        ("hello@world", "HeLlO@wOrLd"),
        ("hello#world", "HeLlO#wOrLd"),
        # punctuation between letters
        ("a!b?c", "A!b?C"),
        ("a-b-c", "A-b-C"),
        ("a_b_c", "A_b_C"),
        ("a.b.c", "A.b.C"),
        ("a/b/c", "A/b/C"),
        ("a+b+c", "A+b+C"),
        ("a=b=c", "A=b=C"),
        ("a:b:c", "A:b:C"),
        ("a;b;c", "A;b;C"),
        ("a,b,c", "A,b,C"),
        # punctuation at beginning/end
        ("!hello", "!HeLlO"),
        ("?hello", "?HeLlO"),
        (".hello", ".HeLlO"),
        ("hello!", "HeLlO!"),
        ("hello?", "HeLlO?"),
        ("!hello!", "!HeLlO!"),
        ("?hello?", "?HeLlO?"),
        ("...hello...", "...HeLlO..."),
        ("---hello---", "---HeLlO---"),
        ("***hello***", "***HeLlO***"),
        # numbers + punctuation
        ("1a2b3c", "1A2b3C"),
        ("1-a-2-b-3-c", "1-A-2-b-3-C"),
        ("42madrid!", "42MaDrId!"),
        ("python3.9 rocks!", "PyThOn3.9 RoCkS!"),
        ("123!abc?456", "123!AbC?456"),
        ("a1!b2?c3", "A1!b2?C3"),
        ("99 bottles", "99 BoTtLeS"),
        ("3blindmice", "3BlInDmIcE"),
        ("version2test", "VeRsIoN2tEsT"),
        ("test123test456test", "TeSt123TeSt456TeSt"),
        # no alphabetic characters
        ("1234567890", "1234567890"),
        ("!@#$%^&*()", "!@#$%^&*()"),
        ("123!@#456", "123!@#456"),
        ("---___---", "---___---"),
        ("...,,,!!!", "...,,,!!!"),
        # longer examples
        (
            "thequickbrownfox",
            "ThEqUiCkBrOwNfOx",
        ),
        (
            "the quick brown fox",
            "ThE qUiCk BrOwN fOx",
        ),
        (
            "abcdefghijklmnopqrstuvwxyz",
            "AbCdEfGhIjKlMnOpQrStUvWxYz",
        ),
        (
            "hello world this is python",
            "HeLlO wOrLd ThIs Is PyThOn",
        ),
        (
            "this is a very long test string",
            "ThIs Is A vErY lOnG tEsT sTrInG",
        ),
        (
            "abcdefghijklmnopqrstuvwxyz 123",
            "AbCdEfGhIjKlMnOpQrStUvWxYz 123",
        ),
        (
            "1234567890abcdefghijklmnopqrstuvwxyz",
            "1234567890AbCdEfGhIjKlMnOpQrStUvWxYz",
        ),
        (
            "hello123world456test789",
            "HeLlO123wOrLd456TeSt789",
        ),
        (
            "a1b2c3d4e5f6",
            "A1b2C3d4E5f6",
        ),
        (
            "Python3.9 is Great!",
            "PyThOn3.9 Is GrEaT!",
        ),
    ]

    for value, expected in cases:
        result = module.alternate_case(value)
        check(f"alternate_case({value!r})", result, expected)
