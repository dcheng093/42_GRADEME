"""Build the Python ranks' subject folders from the 42exam.net snapshots.

    python3 scripts/import_python.py [3 4 5 6]

For every subject in scripts/data/rankNN.json, writes subjects/rankNN/<name>/:
    sub.txt, sub.<lang>.txt   subject (English + translations)
    starter.py                what rendu/ starts with, when the signature is
                              more than one def line (classes, two functions)
    tests.py                  examples + edge cases + seeded random cases, with
                              expected values computed by the reference solution

The reference solution, subjects/rankNN/<name>/solution.py, is written by hand
and only read here. The import stops if it disagrees with a published example.
Extra cases and generators live in scripts/python_cases.py.
"""

import ast
import copy
import json
import random
import re
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import python_cases as pc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts" / "data"
LANGS = ("de", "fr", "es", "it", "ru", "tr", "zh", "ar")
EXAMPLES = {"en": "Examples", "de": "Beispiele", "fr": "Exemples", "es": "Ejemplos", "it": "Esempi",
            "ru": "Примеры", "tr": "Örnekler", "zh": "示例", "ar": "أمثلة"}
SAME_ROOT = "__same_root__"


class ImportError_(Exception):
    pass


# ── reading examples ────────────────────────────────────────────────────────
def _literal(node):
    return ast.literal_eval(node)


def _output(text):
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def parse_call(src):
    """'f(1, "a")' -> ('f', (1, 'a'))"""
    call = ast.parse(src.strip(), mode="eval").body
    return call.func.id, tuple(_literal(a) for a in call.args)


def parse_roundtrip(src):
    """'unpack(pack([...]))' -> ([...],)"""
    outer = ast.parse(src.strip(), mode="eval").body
    inner = outer.args[0]
    return tuple(_literal(a) for a in inner.args)


def parse_script(src):
    """'h = MinHeap(); h.push(5); h.peek()' -> ((), [('push', (5,)), ('peek', ())])"""
    body = ast.parse(src.strip()).body
    first = body[0]
    ctor = tuple(_literal(a) for a in first.value.args)
    ops = []
    for stmt in body[1:]:
        expr = stmt.value
        if isinstance(expr, ast.Compare):  # uf.find(a) == uf.find(b)
            a, b = expr.left, expr.comparators[0]
            ops.append((SAME_ROOT, (_literal(a.args[0]), _literal(b.args[0]))))
        else:
            ops.append((expr.func.attr, tuple(_literal(a) for a in expr.args)))
    return ctor, ops


# ── running the reference ───────────────────────────────────────────────────
def apply_ops(obj, ops):
    results = []
    for method, args in ops:
        if method == SAME_ROOT:
            results.append(obj.find(args[0]) == obj.find(args[1]))
        else:
            results.append(getattr(obj, method)(*copy.deepcopy(args)))
    return results


def _norm(value, unordered):
    if unordered and isinstance(value, (list, tuple)):
        return sorted(value, key=repr)
    return value


# ── writers ─────────────────────────────────────────────────────────────────
def subject_text(task, lang, signature):
    desc = task["description"].get(lang) or task["description"]["en"]
    desc = desc.replace("**", "").replace("$O(", "O(").replace(")$", ")").replace("\\log", "log").strip()
    head = [f"Assignment name  : {task['name']}", f"Expected files   : {task['file']}"]
    if task.get("forbidden"):
        head.append(f"Forbidden functions : {', '.join(task['forbidden'])}")
    lines = head + ["-" * 80, "", desc, "", signature, "", f"{EXAMPLES.get(lang, 'Examples')}:", ""]
    inputs = [e["input"].strip() for e in task["examples"]]
    width = min(max(len(i) for i in inputs), 60)
    for inp, ex in zip(inputs, task["examples"]):
        if len(inp) > width:
            lines += [inp, f"{'':<{width}}  → {ex['output']}"]
        else:
            lines.append(f"{inp:<{width}}  → {ex['output']}")
    return "\n".join(lines) + "\n"


def starter_text(signature):
    """Signature lines turned into a file that imports, with `pass` bodies."""
    lines = []
    if re.search(r"\bAny\b", signature):
        lines += ["from typing import Any", "", ""]
    sig_lines = [l.rstrip() for l in signature.splitlines() if l.strip()]
    for i, line in enumerate(sig_lines):
        indent = len(line) - len(line.lstrip())
        if line.lstrip().startswith("def "):
            if indent == 0 and i and lines and lines[-1] != "":
                lines += ["", ""]
            elif indent and lines and lines[-1].strip() != "" and not lines[-1].lstrip().startswith("class "):
                lines.append("")
            lines += [line, " " * (indent + 4) + "pass"]
        else:
            if i and lines and lines[-1] != "":
                lines += ["", ""]
            lines.append(line)
    return "\n".join(lines) + "\n"


def tests_text(name, task, body_lines, perf):
    out = [f'"""Tests for {name}. Generated by scripts/import_python.py: edit that, not this."""', "",
           "from examshell import pytests", ""]
    if task.get("forbidden"):
        out.append(f"FORBIDDEN = {task['forbidden']!r}")
    out += body_lines
    perf_entries = []
    for i, (description, kind, target, source) in enumerate(perf):
        out += ["", source.replace("def build(rng):", f"def _build_{i}(rng):").rstrip()]
        perf_entries.append(f"    ({description!r}, {kind!r}, {target!r}, _build_{i}),")
    if perf_entries:
        out += ["", "", "PERF = ["] + perf_entries + ["]"]
    return out


def _cases_block(rows):
    return ["CASES = ["] + [f"    {row}," for row in rows] + ["]"]


# ── per kind ────────────────────────────────────────────────────────────────
def build_calls(name, task, ref, functions, rng):
    unordered = name in pc.UNORDERED
    alternates = pc.ALTERNATES.get(name, [])

    def norm_entry(entry):
        if len(functions) == 1:
            return functions[0], tuple(entry)
        return entry[0], tuple(entry[1])

    examples = [parse_call(e["input"]) for e in task["examples"]]
    extra = [norm_entry(e) for e in pc.EDGE.get(name, [])]
    extra += [norm_entry(e) for e in pc.random_cases(name, rng)]

    cases, seen, dropped = [], set(), 0
    for i, (fname, args) in enumerate(examples + extra):
        key = repr((fname, args))
        if key in seen:
            continue
        seen.add(key)
        got = ref[fname](*copy.deepcopy(args))
        if i < len(examples):
            want = _output(task["examples"][i]["output"])
            if _norm(got, unordered) != _norm(want, unordered):
                raise ImportError_(f"{name}: reference gives {got!r} for {task['examples'][i]['input'].strip()},"
                                   f" the subject says {task['examples'][i]['output']}")
        elif any(_norm(alt(*copy.deepcopy(args)), unordered) != _norm(got, unordered) for alt in alternates):
            dropped += 1
            continue
        cases.append((fname, args, got))
    rows = [repr(c) for c in cases]
    flags = []
    if unordered:
        flags.append("unordered=True")
    if name in pc.NO_MUTATION:
        flags.append("no_mutation=True")
    body = [""] + _cases_block(rows) + ["", "", "def run(module, check):",
                                        f"    pytests.run_calls(module, check, CASES{''.join(', ' + f for f in flags)})"]
    return body, len(cases), dropped


def build_class(name, task, ref, rng):
    cls_name, var = pc.CLASSES[name]
    cls = ref[cls_name]
    scripts = [parse_script(e["input"]) for e in task["examples"]]
    cases = []
    for i, (ctor, ops) in enumerate(scripts + pc.class_cases(name, rng)):
        results = apply_ops(cls(*ctor), ops)
        if i < len(scripts):
            want = _output(task["examples"][i]["output"])
            if results[-1] != want:
                raise ImportError_(f"{name}: reference gives {results[-1]!r} for {task['examples'][i]['input']},"
                                   f" the subject says {task['examples'][i]['output']}")
        cases.append((ctor, ops, results))
    body = [""] + _cases_block([repr(c) for c in cases]) + [
        "", "", "def run(module, check):",
        f"    pytests.run_class(module, check, {cls_name!r}, {var!r}, CASES)"]
    return body, len(cases), 0


def build_roundtrip(name, task, ref, rng):
    enc, dec = pc.ROUNDTRIP[name]
    values = [parse_roundtrip(e["input"]) for e in task["examples"]]
    for value, ex in zip(values, task["examples"]):
        got = ref[dec](ref[enc](copy.deepcopy(value[0])))
        if got != _output(ex["output"]):
            raise ImportError_(f"{name}: reference round-trip gives {got!r}, the subject says {ex['output']}")
    cases, seen = [], set()
    for value in values + pc.EDGE.get(name, []) + pc.random_cases(name, rng):
        if repr(value) not in seen:
            seen.add(repr(value))
            cases.append(value)
    body = [""] + _cases_block([repr(c) for c in cases]) + [
        "", "", "def run(module, check):",
        f"    pytests.run_roundtrip(module, check, {enc!r}, {dec!r}, CASES)"]
    return body, len(cases), 0


# ── main ────────────────────────────────────────────────────────────────────
def import_rank(rank):
    tasks = json.loads((DATA / f"rank{rank:02d}.json").read_text(encoding="utf-8"))
    out = ROOT / "subjects" / f"rank{rank:02d}"
    print(f"rank{rank:02d}")
    for task in sorted(tasks, key=lambda t: (t["level"], t["id"])):
        name = task["name"]
        if name in pc.FORBIDDEN:
            task = dict(task, forbidden=pc.FORBIDDEN[name])
        folder = out / name
        solution = folder / "solution.py"
        if not solution.is_file():
            raise ImportError_(f"{name}: write the reference first: {solution.relative_to(ROOT)}")
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

        (folder / "tests.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (folder / "sub.txt").write_text(subject_text(task, "en", signature), encoding="utf-8")
        for lang in LANGS:
            if task["description"].get(lang):
                (folder / f"sub.{lang}.txt").write_text(subject_text(task, lang, signature), encoding="utf-8")
        starter = folder / "starter.py"
        if len(signature.strip().splitlines()) > 1 or "Any" in signature:
            starter.write_text(starter_text(signature), encoding="utf-8")
        elif starter.exists():
            starter.unlink()
        note = f"  ({dropped} ambiguous dropped)" if dropped else ""
        perf_note = f" + {len(perf)} speed" if perf else ""
        print(f"  L{task['level']}  {name:<32} {count:>3} cases{perf_note}{note}")


def main(argv):
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
