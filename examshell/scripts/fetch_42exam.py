"""Snapshot the subject data of 42exam.net into
examshell/scripts/data/rankNN.json.

    python3 examshell/scripts/fetch_42exam.py [2 3 4 5 6]

Each rank site (https://rankNN.42exam.net/) ships its subjects as a JavaScript
file, js/data.js, holding `var SUBJECTS = [ {...}, ... ];`. This converts that
object literal to JSON with a small tokenizer: the JavaScript is never run.

The snapshots are committed, so importing is offline and reproducible:
re-run this only when you want newer subjects, then re-run the importers and
review the diff.
"""

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
OUT = SCRIPTS / "data"
URL = "https://rank{:02d}.42exam.net/js/data.js"


def js_literal_to_json(src: str) -> Any:
    """The first [...] after `SUBJECTS =` in `src`, as Python data.

    Handles what the files use: unquoted keys, double-quoted strings, trailing
    commas and // or /* */ comments.
    """
    start = src.index("[", src.index("SUBJECTS"))
    out: list[str] = []
    i, depth = start, 0
    while i < len(src):
        ch = src[i]
        if ch == '"' or ch == "'":
            j = i + 1
            buf: list[str] = []
            while src[j] != ch:
                if src[j] == "\\":
                    nxt = src[j + 1]
                    buf.append("'" if nxt == "'" else "\\" + nxt)
                    j += 2
                    continue
                buf.append('\\"' if src[j] == '"' else src[j])
                j += 1
            out.append('"' + "".join(buf) + '"')
            i = j + 1
            continue
        if src.startswith("//", i):
            i = src.index("\n", i)
            continue
        if src.startswith("/*", i):
            i = src.index("*/", i) + 2
            continue
        if ch.isalpha() or ch == "_" or ch == "$":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            word = src[i:j]
            k = j
            while src[k] in " \t\r\n":
                k += 1
            if src[k] == ":":
                out.append(json.dumps(word))
            elif word in ("true", "false", "null"):
                out.append(word)
            else:
                raise ValueError(f"unexpected identifier {word!r} at {i}")
            i = j
            continue
        if ch == ",":
            k = i + 1
            while k < len(src) and (
                src[k] in " \t\r\n" or src.startswith("//", k)
            ):
                k = src.index("\n", k) if src.startswith("//", k) else k + 1
            if src[k] in "]}":
                i += 1  # trailing comma
                continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                out.append(ch)
                break
        out.append(ch)
        i += 1
    return json.loads("".join(out))


def fetch(rank: int) -> None:
    req = urllib.request.Request(
        URL.format(rank), headers={"User-Agent": "examshell-fetch"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        src = resp.read().decode("utf-8")
    data = js_literal_to_json(src)
    for task in data:
        task["level"] = int(task["level"])
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"rank{rank:02d}.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"rank{rank:02d}: {len(data)} subjects -> {path.relative_to(ROOT)}")


def main(argv: list[str]) -> int:
    ranks = [int(a) for a in argv[1:]] or [2, 3, 4, 5, 6]
    for rank in ranks:
        fetch(rank)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
