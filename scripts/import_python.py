"""Build the Python ranks' subject folders from the 42exam.net snapshots.

    python3 scripts/import_python.py [3 4 5 6]

For every subject in scripts/data/rankNN.json, writes subjects/rankNN/<name>/:
    sub.txt, sub.<lang>.txt   subject (English + translations)
    starter.py                what rendu/ starts with, when the signature is
                              more than one def line (classes, two functions)
    tests.py                  examples + edge cases + seeded random cases,
                              with expected values computed by the reference
                              solution

The reference solution, subjects/rankNN/<name>/solution.py, is written by hand
and only read here. The import stops if it disagrees with a published example.
Extra cases and generators live in scripts/python_cases.py.

The files written pass flake8 and mypy (the 42 flags), like the rest of the
repo.
"""

import ast
import copy
import json
import pprint
import random
import re
import runpy
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import python_cases as pc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts" / "data"
LANGS = ("de", "fr", "es", "it", "ru", "tr", "zh", "ar")
EXAMPLES = {
    "en": "Examples",
    "de": "Beispiele",
    "fr": "Exemples",
    "es": "Ejemplos",
    "it": "Esempi",
    "ru": "Примеры",
    "tr": "Örnekler",
    "zh": "示例",
    "ar": "أمثلة",
}
SAME_ROOT = "__same_root__"
MAX_LINE = 79  # flake8's default

# a subject from scripts/data/rankNN.json
Task = dict[str, Any]
# what a reference solution.py defines, by name
Ref = dict[str, Any]
# (tests.py lines after the imports, number of cases, ambiguous dropped)
Built = tuple[list[str], int, int]


class ImportError_(Exception):
    pass


# ── reading examples ────────────────────────────────────────────────────────
def _literal(node: ast.expr) -> Any:
    return ast.literal_eval(node)


def _output(text: str) -> Any:
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def _call(node: ast.AST, src: str) -> ast.Call:
    if not isinstance(node, ast.Call):
        raise ImportError_(f"not a call: {src.strip()!r}")
    return node


def parse_call(src: str) -> tuple[str, tuple[Any, ...]]:
    """'f(1, "a")' -> ('f', (1, 'a'))"""
    call = _call(ast.parse(src.strip(), mode="eval").body, src)
    if not isinstance(call.func, ast.Name):
        raise ImportError_(f"not a plain function call: {src.strip()!r}")
    return call.func.id, tuple(_literal(a) for a in call.args)


def parse_roundtrip(src: str) -> tuple[Any, ...]:
    """'unpack(pack([...]))' -> ([...],)"""
    outer = _call(ast.parse(src.strip(), mode="eval").body, src)
    inner = _call(outer.args[0], src)
    return tuple(_literal(a) for a in inner.args)


def parse_script(src: str) -> tuple[tuple[Any, ...], list[pc.Op]]:
    """'h = MinHeap(); h.push(5); h.peek()'
    -> ((), [('push', (5,)), ('peek', ())])"""
    body = ast.parse(src.strip()).body
    first = body[0]
    if not isinstance(first, ast.Assign):
        raise ImportError_(f"should start with an assignment: {src!r}")
    ctor = tuple(_literal(a) for a in _call(first.value, src).args)
    ops: list[pc.Op] = []
    for stmt in body[1:]:
        if not isinstance(stmt, ast.Expr):
            raise ImportError_(f"unexpected statement in {src!r}")
        expr = stmt.value
        if isinstance(expr, ast.Compare):  # uf.find(a) == uf.find(b)
            a = _call(expr.left, src)
            b = _call(expr.comparators[0], src)
            ops.append(
                (SAME_ROOT, (_literal(a.args[0]), _literal(b.args[0])))
            )
        else:
            call = _call(expr, src)
            if not isinstance(call.func, ast.Attribute):
                raise ImportError_(f"not a method call in {src!r}")
            ops.append(
                (call.func.attr, tuple(_literal(a) for a in call.args))
            )
    return ctor, ops


# ── running the reference ───────────────────────────────────────────────────
def apply_ops(obj: Any, ops: list[pc.Op]) -> list[Any]:
    results = []
    for method, args in ops:
        if method == SAME_ROOT:
            results.append(obj.find(args[0]) == obj.find(args[1]))
        else:
            results.append(getattr(obj, method)(*copy.deepcopy(args)))
    return results


def _norm(value: Any, unordered: bool) -> Any:
    if unordered and isinstance(value, (list, tuple)):
        return sorted(value, key=repr)
    return value


# ── writers ─────────────────────────────────────────────────────────────────
def subject_text(task: Task, lang: str, signature: str) -> str:
    desc = task["description"].get(lang) or task["description"]["en"]
    desc = (
        desc.replace("**", "")
        .replace("$O(", "O(")
        .replace(")$", ")")
        .replace("\\log", "log")
        .strip()
    )
    head = [
        f"Assignment name  : {task['name']}",
        f"Expected files   : {task['file']}",
    ]
    if task.get("forbidden"):
        head.append(f"Forbidden functions : {', '.join(task['forbidden'])}")
    lines = head + [
        "-" * 80,
        "",
        desc,
        "",
        signature,
        "",
        f"{EXAMPLES.get(lang, 'Examples')}:",
        "",
    ]
    inputs = [e["input"].strip() for e in task["examples"]]
    width = min(max(len(i) for i in inputs), 60)
    for inp, ex in zip(inputs, task["examples"]):
        if len(inp) > width:
            lines += [inp, f"{'':<{width}}  → {ex['output']}"]
        else:
            lines.append(f"{inp:<{width}}  → {ex['output']}")
    return "\n".join(lines) + "\n"


def _stub_body(def_line: str) -> str:
    """`pass` where mypy accepts it (no return value), else
    `raise NotImplementedError`."""
    returns = re.search(r"->\s*(.+?)\s*:\s*$", def_line)
    if not returns or returns.group(1) == "None":
        return "pass"
    return "raise NotImplementedError"


def starter_text(signature: str) -> str:
    """Signature lines turned into a file that imports, with stub bodies."""
    lines = []
    if re.search(r"\bAny\b", signature):
        lines += ["from typing import Any", "", ""]
    sig_lines = [
        line.rstrip() for line in signature.splitlines() if line.strip()
    ]
    for i, line in enumerate(sig_lines):
        indent = len(line) - len(line.lstrip())
        if line.lstrip().startswith("def "):
            if indent == 0 and i and lines and lines[-1] != "":
                lines += ["", ""]
            elif (
                indent
                and lines
                and lines[-1].strip() != ""
                and not lines[-1].lstrip().startswith("class ")
            ):
                lines.append("")
            if "def __init__(" in line and "->" not in line:
                line = re.sub(r"\)\s*:\s*$", ") -> None:", line)
            lines += [line, " " * (indent + 4) + _stub_body(line)]
        else:
            if i and lines and lines[-1] != "":
                lines += ["", ""]
            lines.append(line)
    return "\n".join(lines) + "\n"


def tests_text(
    name: str,
    task: Task,
    body_lines: list[str],
    perf: list[tuple[str, str, str, str]],
) -> list[str]:
    out = [
        f'"""Tests for {name}.',
        "",
        "Generated by scripts/import_python.py: edit that, not this.",
        '"""',
        "",
    ]
    if perf:
        out.append("import random")
    out += [
        "from types import ModuleType",
        "from typing import Any",
        "",
        "from examshell import pytests",
        "",
    ]
    if task.get("forbidden"):
        out.append(f"FORBIDDEN = {task['forbidden']!r}")
    out += body_lines
    perf_entries = []
    for i, (description, kind, target, source) in enumerate(perf):
        out += [
            "",
            "",
            source.replace("def build(", f"def _build_{i}(").rstrip(),
        ]
        entry = f"    ({description!r}, {kind!r}, {target!r}, _build_{i}),"
        if len(entry) > MAX_LINE:
            entry = "\n".join([
                "    (",
                f"        {description!r},",
                f"        {kind!r},",
                f"        {target!r},",
                f"        _build_{i},",
                "    ),",
            ])
        perf_entries.append(entry)
    if perf_entries:
        out += ["", "", "PERF = ["] + perf_entries + ["]"]
    return out


def _split_str(text: str, indent: int) -> list[str]:
    """A long string as adjacent literals, one per line (Python joins
    them)."""
    pieces = [""]
    for ch in text:
        if indent + len(repr(pieces[-1] + ch)) + 1 > MAX_LINE:
            pieces.append("")
        pieces[-1] += ch
    return [" " * indent + repr(p) for p in pieces]


def _literal_lines(value: object, indent: int) -> list[str]:
    """`value` as Python source lines, none longer than MAX_LINE - 1 (room
    for the comma that follows). Used when pprint can't make it fit."""
    pad = " " * indent
    if indent + len(repr(value)) + 1 <= MAX_LINE:
        return [pad + repr(value)]
    if isinstance(value, str):
        return _split_str(value, indent)
    lines: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            lines.append(f"{pad}    {k!r}:")
            lines += _literal_lines(v, indent + 8)
            lines[-1] += ","
        return [pad + "{"] + lines + [pad + "}"]
    if isinstance(value, (list, tuple)):
        for item in value:
            lines += _literal_lines(item, indent + 4)
            lines[-1] += ","
        if isinstance(value, list):
            return [pad + "["] + lines + [pad + "]"]
        return [pad + "("] + lines + [pad + ")"]
    return [pad + repr(value)]  # nothing shorter exists


def _row(value: object) -> list[str]:
    """One CASES entry, wrapped to fit in MAX_LINE columns."""
    text = f"    {value!r},"
    if len(text) <= MAX_LINE:
        return [text]
    pretty = pprint.pformat(
        value, width=MAX_LINE - 5, compact=True, sort_dicts=False
    )
    lines = ["    " + line for line in pretty.splitlines()]
    if any(len(line) >= MAX_LINE for line in lines):
        lines = _literal_lines(value, 4)
    lines[-1] += ","
    return lines


def _cases_block(type_hint: str, cases: list[Any]) -> list[str]:
    lines = [f"CASES: {type_hint} = ["]
    for case in cases:
        lines += _row(case)
    return lines + ["]"]


def _run(call: str) -> list[str]:
    """def run(...), calling `call` (pytests.run_xxx(module, check, ...))."""
    return [
        "",
        "",
        "def run(module: ModuleType, check: pytests.Check) -> None:",
        f"    {call}",
    ]


# ── per kind ────────────────────────────────────────────────────────────────
def build_calls(
    name: str,
    task: Task,
    ref: Ref,
    functions: list[str],
    rng: random.Random,
) -> Built:
    unordered = name in pc.UNORDERED
    alternates = pc.ALTERNATES.get(name, [])

    def norm_entry(entry: pc.Args) -> tuple[str, tuple[Any, ...]]:
        if len(functions) == 1:
            return functions[0], tuple(entry)
        return entry[0], tuple(entry[1])

    examples = [parse_call(e["input"]) for e in task["examples"]]
    extra = [norm_entry(e) for e in pc.EDGE.get(name, [])]
    extra += [norm_entry(e) for e in pc.random_cases(name, rng)]

    cases: list[tuple[str, tuple[Any, ...], Any]] = []
    seen: set[str] = set()
    dropped = 0
    for i, (fname, args) in enumerate(examples + extra):
        key = repr((fname, args))
        if key in seen:
            continue
        seen.add(key)
        got = ref[fname](*copy.deepcopy(args))
        if i < len(examples):
            want = _output(task["examples"][i]["output"])
            if _norm(got, unordered) != _norm(want, unordered):
                raise ImportError_(
                    f"{name}: reference gives {got!r} for"
                    f" {task['examples'][i]['input'].strip()}, the subject"
                    f" says {task['examples'][i]['output']}"
                )
        elif any(
            _norm(alt(*copy.deepcopy(args)), unordered)
            != _norm(got, unordered)
            for alt in alternates
        ):
            dropped += 1
            continue
        cases.append((fname, args, got))
    flags = []
    if unordered:
        flags.append("unordered=True")
    if name in pc.NO_MUTATION:
        flags.append("no_mutation=True")
    extra_args = "".join(", " + f for f in flags)
    body = (
        [""]
        + _cases_block("list[tuple[str, tuple[Any, ...], Any]]", cases)
        + _run(f"pytests.run_calls(module, check, CASES{extra_args})")
    )
    return body, len(cases), dropped


def build_class(name: str, task: Task, ref: Ref, rng: random.Random) -> Built:
    cls_name, var = pc.CLASSES[name]
    cls = ref[cls_name]
    scripts = [parse_script(e["input"]) for e in task["examples"]]
    cases = []
    for i, (ctor, ops) in enumerate(scripts + pc.class_cases(name, rng)):
        results = apply_ops(cls(*ctor), ops)
        if i < len(scripts):
            want = _output(task["examples"][i]["output"])
            if results[-1] != want:
                raise ImportError_(
                    f"{name}: reference gives {results[-1]!r} for"
                    f" {task['examples'][i]['input']}, the subject says"
                    f" {task['examples'][i]['output']}"
                )
        cases.append((ctor, ops, results))
    hint = "list[tuple[tuple[Any, ...], list[pytests.Op], list[Any]]]"
    run_class = f"pytests.run_class(module, check, {cls_name!r}, {var!r}"
    body = [""] + _cases_block(hint, cases) + _run(run_class + ", CASES)")
    return body, len(cases), 0


def build_roundtrip(
    name: str, task: Task, ref: Ref, rng: random.Random
) -> Built:
    enc, dec = pc.ROUNDTRIP[name]
    values = [parse_roundtrip(e["input"]) for e in task["examples"]]
    for value, ex in zip(values, task["examples"]):
        got = ref[dec](ref[enc](copy.deepcopy(value[0])))
        if got != _output(ex["output"]):
            raise ImportError_(
                f"{name}: reference round-trip gives {got!r}, the subject"
                f" says {ex['output']}"
            )
    cases: list[tuple[Any, ...]] = []
    seen: set[str] = set()
    for value in values + pc.EDGE.get(name, []) + pc.random_cases(name, rng):
        if repr(value) not in seen:
            seen.add(repr(value))
            cases.append(value)
    run_roundtrip = f"pytests.run_roundtrip(module, check, {enc!r}, {dec!r}"
    body = (
        [""]
        + _cases_block("list[tuple[Any]]", cases)
        + _run(run_roundtrip + ", CASES)")
    )
    return body, len(cases), 0


# ── main ────────────────────────────────────────────────────────────────────
def import_rank(rank: int) -> None:
    tasks = json.loads(
        (DATA / f"rank{rank:02d}.json").read_text(encoding="utf-8")
    )
    out = ROOT / "subjects" / f"rank{rank:02d}"
    print(f"rank{rank:02d}")
    for task in sorted(tasks, key=lambda t: (t["level"], t["id"])):
        name = task["name"]
        if name in pc.FORBIDDEN:
            task = dict(task, forbidden=pc.FORBIDDEN[name])
        folder = out / name
        solution = folder / "solution.py"
        if not solution.is_file():
            raise ImportError_(
                f"{name}: write the reference first:"
                f" {solution.relative_to(ROOT)}"
            )
        ref = runpy.run_path(str(solution))
        signature = pc.SIGNATURES.get(name, task["signature"])
        functions = re.findall(r"^def (\w+)\(", signature, re.MULTILINE)
        rng = random.Random(name)

        if name in pc.CLASSES:
            body, count, dropped = build_class(name, task, ref, rng)
        elif name in pc.ROUNDTRIP:
            body, count, dropped = build_roundtrip(name, task, ref, rng)
        else:
            body, count, dropped = build_calls(name, task, ref, functions, rng)

        perf = pc.PERF.get(name, [])
        if perf:
            body.append("    pytests.run_perf(module, check, __file__, PERF)")
        lines = tests_text(name, task, body, perf)

        (folder / "tests.py").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        (folder / "sub.txt").write_text(
            subject_text(task, "en", signature), encoding="utf-8"
        )
        for lang in LANGS:
            if task["description"].get(lang):
                (folder / f"sub.{lang}.txt").write_text(
                    subject_text(task, lang, signature), encoding="utf-8"
                )
        starter = folder / "starter.py"
        if len(signature.strip().splitlines()) > 1 or "Any" in signature:
            starter.write_text(starter_text(signature), encoding="utf-8")
        elif starter.exists():
            starter.unlink()
        note = f"  ({dropped} ambiguous dropped)" if dropped else ""
        perf_note = f" + {len(perf)} speed" if perf else ""
        print(
            f"  L{task['level']}  {name:<32} {count:>3} cases{perf_note}{note}"
        )


def main(argv: list[str]) -> int:
    ranks = [int(a) for a in argv[1:]] or [3, 4, 5, 6]
    try:
        for rank in ranks:
            import_rank(rank)
    except ImportError_ as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
