def run(module, check):
    cases = [
        # basic valid
        ("", True),
        ("()", True),
        ("[]", True),
        ("{}", True),
        ("abc", True),
        ("123", True),
        ("hello world", True),
        ("a(b)c", True),
        ("a[b]c", True),
        ("a{b}c", True),

        # basic invalid
        ("(", False),
        (")", False),
        ("[", False),
        ("]", False),
        ("{", False),
        ("}", False),
        (")(", False),
        ("][", False),
        ("}{", False),
        ("([)", False),

        # simple matching
        ("()[]{}", True),
        ("[](){}", True),
        ("{}[]()", True),
        ("(){}", True),
        ("[]{}", True),
        ("{}()", True),
        ("()[]", True),
        ("[]()", True),
        ("{}[]", True),
        ("({})", True),

        # nested brackets
        ("(())", True),
        ("[[]]", True),
        ("{{}}", True),
        ("((()))", True),
        ("[[[]]]", True),
        ("{{{}}}", True),
        ("(([]))", True),
        ("[({})]", True),
        ("{[()]}", True),
        ("({[]})", True),

        # deep nesting
        ("(((())))", True),
        ("[[[[]]]]", True),
        ("{{{{}}}}", True),
        ("([({})])", True),
        ("{[({[]})]}", True),
        ("((([[]])))", True),
        ("[[({})]]", True),
        ("{{[()]}}", True),
        ("([{()}])", True),
        ("{({[]})}", True),

        # wrong bracket types
        ("(]", False),
        ("[)", False),
        ("{)", False),
        ("(}", False),
        ("[}", False),
        ("{]", False),
        ("([)]", False),
        ("[(])", False),
        ("{[}]", False),
        ("{(])}", False),

        # extra closing brackets
        (")()", False),
        ("())", False),
        ("())()", False),
        ("][]", False),
        ("[]]", False),
        ("}{}", False),
        ("{}}", False),
        ("abc)", False),
        ("abc]", False),
        ("abc}", False),

        # extra opening brackets
        ("(()", False),
        ("[[]", False),
        ("{{}", False),
        ("((())", False),
        ("[[[]]", False),
        ("{{{}}", False),
        ("abc(", False),
        ("abc[", False),
        ("abc{", False),
        ("hello(world", False),

        # text inside brackets
        ("(abc)", True),
        ("[abc]", True),
        ("{abc}", True),
        ("(hello world)", True),
        ("[hello world]", True),
        ("{hello world}", True),
        ("(a[b]c)", True),
        ("[a{b}c]", True),
        ("{a(b)c}", True),
        ("a(b[c]d)e", True),

        # numbers and symbols
        ("(123)", True),
        ("[123]", True),
        ("{123}", True),
        ("(1[2]3)", True),
        ("[1{2}3]", True),
        ("{1(2)3}", True),
        ("abc{123[xyz]}", True),
        ("abc{[123(xyz)]}", True),
        ("[{adaudna}]", True),
        ("[{adaudna}])", False),

        # spaces and newlines
        ("( )", True),
        ("[ ]", True),
        ("{ }", True),
        ("( [ ] )", True),
        ("{ [ ( ) ] }", True),
        ("hello ( world )", True),
        ("hello [ world ]", True),
        ("hello { world }", True),
        ("(hello [world] test)", True),
        ("( hello [ world ]", False),

        # mixed valid
        ("a(b[c]d)e", True),
        ("a{b[c(d)e]f}g", True),
        ("x(y[z{abc}])", True),
        ("[{()}]", True),
        ("{[()]}", True),
        ("([{}])", True),
        ("{[()()]}", True),
        ("((a)[b]{c})", True),
        ("a(b)c[d]e{f}", True),
        ("abc{[123(xyz)]}", True),

        # mixed invalid
        ("a(b[c)d]e", False),
        ("a{b[c}d]e", False),
        ("x(y[z})]", False),
        ("[{()}]", True),
        ("{[(])}", False),
        ("([{}]", False),
        ("[{}))", False),
        ("{{[()]}", False),
        ("abc{[123(xyz]}]", False),
        ("[{adaudna}])", False),

        # more edge cases
        ("((((()))))", True),
        ("[[[[[]]]]]", True),
        ("{{{{{}}}}}", True),
        ("()()()()()", True),
        ("[][][][][]", True),
        ("{}{}{}{}{}", True),
        ("([{}])([{}])", True),
        ("(([]){})", True),
        ("{([][])}", True),
        ("([[[{{{}}}]]])", True),
    ]

    for value, expected in cases:
        result = module.brackets(value)
        check(
            f"brackets({value!r})",
            result,
            expected
        )
