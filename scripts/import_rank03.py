"""Import the current Rank 03 pool from an examshell_python package checkout.

    python3 scripts/import_rank03.py [path/to/examshell_python-X.Y.Z]

For every task in src/examshell/data/rank3.json, writes subjects/rank03/<name>/:
    sub.txt, sub.<lang>.txt   subject (English + translations)
    solution.py               reference solution from exam42/solutions/
    tests.py                  examples + edge cases + seeded random cases,
                              expected values computed with the reference solution
Re-running overwrites those files.
"""

import ast
import copy
import json
import random
import runpy
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "subjects" / "rank03"
LANGS = ("de", "fr", "es", "it", "ru", "tr", "zh", "ar")
EXAMPLES = {"en": "Examples", "de": "Beispiele", "fr": "Exemples", "es": "Ejemplos", "it": "Esempi",
            "ru": "Примеры", "tr": "Örnekler", "zh": "示例", "ar": "أمثلة"}


# ── extra cases, as argument tuples ─────────────────────────────────────────
def _word(rng, alphabet, lo=0, hi=12):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(lo, hi)))


def _random_cases(name, rng):
    letters, digits = string.ascii_letters, string.digits
    if name == "py_bracket_validator":
        out = []
        for _ in range(40):
            out.append((_word(rng, "()[]{}ab ", 0, 14),))
        for _ in range(10):  # guaranteed-valid nests
            s = ""
            for _ in range(rng.randint(1, 6)):
                o, c = rng.choice(["()", "[]", "{}"])
                s = rng.choice([o + s + c, s + o + c, o + c + s])
            out.append((s,))
        return out
    if name == "py_cryptic_sorter":
        return [([_word(rng, "abcAEoUz", 0, 5) for _ in range(rng.randint(0, 9))],) for _ in range(30)]
    if name == "py_echo_validator":
        out = []
        for _ in range(20):
            half = _word(rng, "abcAB", 1, 6)
            mid = rng.choice(["", "x", "Z"])
            s = half + mid + half[::-1]
            s = "".join(c.upper() if rng.random() < 0.3 else c for c in s)
            s = "".join(c + (rng.choice(" ,.!1") if rng.random() < 0.2 else "") for c in s)
            out.append((s,))
        out += [(_word(rng, "abc ", 1, 8),) for _ in range(15)]
        return out
    if name == "py_mirror_matrix":
        out = []
        for _ in range(20):
            w = rng.randint(1, 6)
            out.append(([[rng.randint(-50, 50) for _ in range(w)] for _ in range(rng.randint(1, 5))],))
        return out
    if name == "py_hidenp":
        return [(_word(rng, "abc", 0, 4), _word(rng, "abcd1", 0, 10)) for _ in range(40)]
    if name == "py_inter":
        return [(_word(rng, "abcdeAB1 ", 0, 10), _word(rng, "abcxyzA ", 0, 10)) for _ in range(40)]
    if name == "py_number_base_converter":
        out = []
        for _ in range(40):
            n, fb, tb = rng.randint(0, 10 ** 9), rng.randint(2, 36), rng.randint(2, 36)
            s = ""
            while True:
                n, r = divmod(n, fb)
                s = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[r] + s
                if not n:
                    break
            out.append((s, fb, tb))
        return out
    if name == "py_pattern_tracker":
        return [(_word(rng, digits + "ab", 0, 16),) for _ in range(40)]
    if name == "py_anagram":
        out = []
        for _ in range(20):
            a = _word(rng, "abcdeABC ", 1, 10)
            b = list(a.replace(" ", ""))
            rng.shuffle(b)
            b = "".join(c.swapcase() if rng.random() < 0.3 else c for c in b)
            if rng.random() < 0.4:
                b += rng.choice("ab")
            out.append((a, b))
        return out
    if name == "py_shadow_merge":
        return [(sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 8))),
                 sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 8)))) for _ in range(30)]
    if name == "py_string_permutation_checker":
        out = []
        for _ in range(20):
            a = _word(rng, "abcAB ,!", 0, 10)
            b = list(a)
            rng.shuffle(b)
            b = "".join(b)
            if rng.random() < 0.4 and b:
                b = b[:-1] + rng.choice("aAz ")
            out.append((a, b))
        return out
    if name == "py_string_sculptor":
        return [(_word(rng, letters + digits + " .!,", 0, 20),) for _ in range(30)]
    if name == "py_twist_sequence":
        return [([rng.randint(-9, 9) for _ in range(rng.randint(0, 8))], rng.randint(0, 20)) for _ in range(30)]
    if name == "py_whisper_cipher":
        return [(_word(rng, letters + digits + " !.", 0, 20), rng.randint(-60, 60)) for _ in range(30)]
    return []


EDGE = {
    "py_bracket_validator": [("a",), ("(",), (")",), ("{[()()]}",), ("((((((((((",), ("([]{}){}[()]",),
                             ("}{",), ("[(])",), ("text with (brackets [and {nesting}])",), ("([)",)],
    "py_cryptic_sorter": [(["b", "a"],), (["B", "a"],), (["a", "A", "a"],), (["zz", "a", "Bb", "aa"],),
                          (["abc", "ABC", "aBc"],), (["one", "two", "six", "ten"],), (["", "a", ""],),
                          (["Zebra", "apple", "Mango", "kiwi", "fig"],)],
    "py_echo_validator": [("a",), ("Aa",), ("ab",), ("No lemon, no melon",), ("Step on no pets",),
                          ("12321",), ("a1b2a",), ("Never odd or even",), ("abca",), ("!!!",)],
    "py_mirror_matrix": [([],), ([[]],), ([[1], [2], [3]],), ([[0, 0], [0, 0]],), ([[1, 2, 3], [4, 5, 6], [7, 8, 9]],)],
    "py_hidenp": [("", ""), ("a", ""), ("a", "a"), ("A", "a"), ("abc", "abc"), ("abc", "cba"),
                  ("aab", "ab"), ("ab", "aab"), ("xyz", "x y z")],
    "py_inter": [("", ""), ("abc", ""), ("aaa", "a"), ("abc", "cba"), ("Aa", "a"), ("a b", " "),
                 ("padinton", "paqefwtdjetyiytjneytjoeyjnejeyj")],
    "py_number_base_converter": [("0", 10, 2), ("0", 2, 36), ("1", 2, 2), ("10", 10, 10), ("ZZ", 36, 10),
                                 ("1295", 10, 36), ("777", 8, 2), ("11111111", 2, 16), ("0010", 2, 10),
                                 ("2", 2, 10), ("1", 10, 37), ("1", 37, 10), ("1", 0, 10), ("", 10, 2),
                                 ("12a", 10, 2), ("1.5", 10, 2), ("4294967295", 10, 16)],
    "py_pattern_tracker": [("",), ("1",), ("12",), ("21",), ("90",), ("89",), ("0123456789",),
                           ("1 2",), ("1212",), ("a1b23c45",)],
    "py_anagram": [("a", "A"), ("a", "b"), (" ", ""), ("abc", "ab"), ("aab", "abb"),
                   ("Astronomer", "Moon starer"), ("The eyes", "They see"), ("abc", "cba ")],
    "py_shadow_merge": [([], []), ([1], []), ([5], [1]), ([-3, 0], [-5, -1, 7]), ([2, 2, 2], [2, 2]),
                        ([1, 2, 3], [1, 2, 3]), ([10, 20, 30], [1, 2, 3])],
    "py_string_permutation_checker": [("a", "a"), ("a", "A"), (" ", ""), ("ab", "ba "), ("aab", "abb"),
                                      ("a!b", "b!a"), ("dormitory", "dirty room")],
    "py_string_sculptor": [("a",), ("A",), ("   ",), ("123",), ("a b c",), ("ab  cd",),
                           ("HELLO WORLD",), ("x1y2z3",), ("Hi! How are you?",)],
    "py_twist_sequence": [([1], 0), ([1], 100), ([1, 2], 1), ([1, 2], 2), ([1, 2, 3, 4, 5], 5),
                          ([1, 2, 3, 4, 5], 7), ([0, 0, 1], 1), ([], 0)],
    "py_whisper_cipher": [("a", 1), ("z", 1), ("Z", 1), ("a", 26), ("a", 52), ("abc", 0), ("abc", -26),
                          ("Hello, World!", 13), ("Uryyb, Jbeyq!", -13), ("1234 !?", 7), ("aZ", -1)],
}
NO_MUTATION = {"py_mirror_matrix"}  # subject says "return a new matrix"


# ── writers ─────────────────────────────────────────────────────────────────
def _subject(task, lang):
    desc = task["description"].get(lang) or task["description"]["en"]
    desc = desc.replace("**", "").strip()
    head = [f"Assignment name  : {task['name']}", f"Expected files   : {task['file']}"]
    if task.get("forbidden"):
        head.append(f"Forbidden functions : {', '.join(task['forbidden'])}")
    lines = head + ["-" * 80, "", desc, "", task["signature"], "", f"{EXAMPLES.get(lang, 'Examples')}:", ""]
    width = max(len(e["input"]) for e in task["examples"])
    lines += [f"{e['input']:<{width}}  → {e['output']}" for e in task["examples"]]
    return "\n".join(lines) + "\n"


def _tests(task, function, cases):
    rows = "\n".join(f"    ({args!r}, {expected!r})," for args, expected in cases)
    forbidden = f"FORBIDDEN = {task['forbidden']!r}\n" if task.get("forbidden") else ""
    mutation = task["name"] in NO_MUTATION
    body = [
        f'"""Tests for {task["name"]}. Generated by scripts/import_rank03.py: edit that, not this."""',
        "",
        "import copy",
        "",
        f"FUNCTION = {function!r}",
        forbidden.rstrip("\n"),
        "CASES = [",
        rows,
        "]",
        "",
        "",
        "def run(module, check):",
        "    fn = getattr(module, FUNCTION)",
        "    for args, expected in CASES:",
        "        call = f\"{FUNCTION}({', '.join(map(repr, args))})\"",
        "        given = copy.deepcopy(args)",
        "        check(call, fn(*given), expected)",
    ]
    if mutation:
        body += ["        check(call + '  must not modify its input', given == args)"]
    return "\n".join(line for line in body if line is not None) + "\n"


def main(argv):
    pkg = Path(argv[1] if len(argv) > 1 else next(ROOT.glob("examshell_python-*"))).resolve()
    tasks = json.loads((pkg / "src/examshell/data/rank3.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        name = task["name"]
        function = task["signature"].split("def ", 1)[1].split("(", 1)[0]
        ref = pkg / "exam42/solutions" / name / task["file"]
        fn = runpy.run_path(str(ref))[function]

        args_list = []
        for ex in task["examples"]:
            call = ast.parse(ex["input"], mode="eval").body
            args_list.append(tuple(ast.literal_eval(a) for a in call.args))
        args_list += EDGE.get(name, [])
        args_list += _random_cases(name, random.Random(name))

        cases, seen = [], set()
        for args in args_list:
            key = repr(args)
            if key in seen:
                continue
            seen.add(key)
            cases.append((args, fn(*copy.deepcopy(args))))

        # the published examples must agree with the reference solution
        for ex, (args, got) in zip(task["examples"], cases):
            try:
                want = ast.literal_eval(ex["output"])
            except (ValueError, SyntaxError):
                want = ex["output"]
            if got != want:
                raise SystemExit(f"{name}: reference gives {got!r} for {ex['input']}, subject says {ex['output']}")

        folder = OUT / name
        folder.mkdir(exist_ok=True)
        (folder / "sub.txt").write_text(_subject(task, "en"), encoding="utf-8")
        for lang in LANGS:
            if task["description"].get(lang):
                (folder / f"sub.{lang}.txt").write_text(_subject(task, lang), encoding="utf-8")
        (folder / "solution.py").write_text(ref.read_text(encoding="utf-8"), encoding="utf-8")
        (folder / "tests.py").write_text(_tests(task, function, cases), encoding="utf-8")
        print(f"  L{int(task['level'])}  {name:<32} {len(cases):>3} cases")


if __name__ == "__main__":
    main(sys.argv)
