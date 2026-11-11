"""Graders must fail wrong answers: each mutant here is a broken answer.

    python3 scripts/selftest.py        (or: make selftest)

`make check` proves every reference passes its tests. This proves the tests
can fail: an off-by-one, a leak, a blocking server, a cheat that prints
"checks passed"... Each mutant is the reference with one change, or a whole
file. Every one of them must be graded as failed.
"""

import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from examshell import config, runner, ui, workspace  # noqa: E402
from examshell.questions import all_questions  # noqa: E402

CHEAT_C = '#include <stdio.h>\nint main(void){printf("  \\u2714 7/7 checks passed\\n");return 0;}\n'
CHEAT_PY = 'print("  14/14 checks passed")\n\ndef inter(s1, s2):\n    return ""\n'
SLOW_WINDOW = '''def sliding_window_maximum(nums, k):
    if k <= 0 or k > len(nums):
        return []
    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]
'''
HEAPQ = '''import heapq


class MinHeap:
    def __init__(self):
        self.d = []

    def push(self, val):
        heapq.heappush(self.d, val)

    def pop(self):
        return heapq.heappop(self.d) if self.d else None

    def peek(self):
        return self.d[0] if self.d else None

    def size(self):
        return len(self.d)
'''
SLOW_LRU = '''class CacheKeeper:
    def __init__(self, capacity):
        self.cap, self.keys, self.d = capacity, [], {}

    def get(self, key):
        if key not in self.d:
            return -1
        self.keys.remove(key)
        self.keys.append(key)
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.keys.remove(key)
        self.keys.append(key)
        self.d[key] = value
        if len(self.keys) > self.cap:
            del self.d[self.keys.pop(0)]
'''
CHUNK_FILTER = '''#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>

int main(int ac, char **av)
{
	char buf[4096];
	ssize_t n;
	size_t pl;

	if (ac != 2 || !av[1][0])
		return 1;
	pl = strlen(av[1]);
	while ((n = read(0, buf, sizeof buf)) > 0)
	{
		char *p = buf, *h;
		while ((h = memmem(p, n - (p - buf), av[1], pl)))
		{
			write(1, p, h - p);
			for (size_t i = 0; i < pl; i++)
				write(1, "*", 1);
			p = h + pl;
		}
		write(1, p, n - (p - buf));
	}
	return 0;
}
'''

# (rank, question, what is wrong, {file: whole content} or {file: [(old, new)]})
MUTANTS = [
    ("rank02", "first_word", "prints 'checks passed' instead of working", {"first_word.c": CHEAT_C}),
    ("rank03", "py_inter", "prints 'checks passed', returns nothing useful", {"py_inter.py": CHEAT_PY}),
    ("rank04", "py_sliding_window_maximum", "O(n*k) instead of O(n)", {"py_sliding_window_maximum.py": SLOW_WINDOW}),
    ("rank06", "min_heap", "uses the forbidden heapq", {"min_heap.py": HEAPQ}),
    ("rank06", "cache_keeper", "O(n) list instead of O(1)", {"cache_keeper.py": SLOW_LRU}),
    ("old_rank05", "bigint", "carry lost on 9+1", {"bigint.cpp": [("carry = d / 10;", "carry = d / 10; if (d == 10) carry = 0;")]}),
    ("old_rank05", "vect2", "leaks in the constructor",
     {"vect2.cpp": [("vect2::vect2() { _c[0] = 0; _c[1] = 0; }",
                     "vect2::vect2() { _c[0] = 0; _c[1] = 0; int *leak = new int[8]; leak[0] = 0; }")]}),
    ("old_rank05", "polyset", "set inserts duplicates", {"set.cpp": [("if (!_bag->has(value))", "if (true)")]}),
    ("old_rank05", "bsq", "never closes the map file", {"bsq.c": [("\t\t\tfclose(file);\n", "")]}),
    ("old_rank05", "life", "wrong survival rule", {"life.c": [("(n == 2 && alive(b, x, y))", "(n == 4 && alive(b, x, y))")]}),
    ("old_rank03", "filter", "only finds matches inside one read() chunk", {"filter.c": CHUNK_FILTER}),
    ("old_rank03", "broken_gnl", "the handout, still broken", "handout"),
    ("old_rank03", "powerset", "skips the empty subset", {"powerset.c": [("\t\tif (sum != target)", "\t\tif (sum != target || !count)")]}),
    ("old_rank03", "tsp", "the handout, tsp() not written", "handout"),
    ("old_rank04", "ft_popen", "the child keeps both pipe ends",
     {"ft_popen.c": [("\t\tclose(fds[0]);\n\t\tclose(fds[1]);\n\t\texecvp", "\t\texecvp")]}),
    ("old_rank04", "picoshell", "the parent keeps the write ends",
     {"picoshell.c": [("\t\tif (fds[1] != -1)\n\t\t\tclose(fds[1]);\n\t\tprev_in", "\t\tprev_in")]}),
    ("old_rank04", "sandbox", "doesn't reap the child after a timeout",
     {"sandbox.c": [("\t\tkill(pid, SIGKILL);\n\t\twaitpid(pid, NULL, 0);", "\t\tkill(pid, SIGKILL);")]}),
    ("old_rank04", "vbc", "+ binds tighter than *",
     {"vbc.c": [("type = MULTI", "type = TMP_ADD"), ("type = ADD", "type = MULTI"), ("type = TMP_ADD", "type = ADD")]}),
    ("old_rank06", "mini_serv", "blocks on a client that never reads",
     {"mini_serv.c": [("fd != except && FD_ISSET(fd, &g_wr)", "fd != except")]}),
    ("old_rank06", "mini_db", "doesn't load the save file", {"mini_db.cpp": [("\tdb.load();\n", "")]}),
]


def _question(rank_key, name):
    for q in all_questions(config.RANKS[rank_key]):
        if q.name == name:
            return q
    raise SystemExit(f"selftest: no question {rank_key}/{name}")


def grade_mutant(rank_key, name, change):
    q = _question(rank_key, name)
    workspace.prepare(q)
    try:
        if change != "handout":
            for f in q.files_in(q.reference_dir):
                src = q.path / "solution.py" if q.is_python else q.reference_dir / f
                shutil.copy(src, q.rendu_dir / f)
            for filename, edit in change.items():
                path = q.rendu_dir / filename
                if isinstance(edit, str):
                    path.write_text(edit)
                    continue
                text = path.read_text()
                for old, new in edit:
                    if old not in text:
                        return None, f"mutation doesn't apply: {old!r}"
                    text = text.replace(old, new)
                path.write_text(text)
        return runner.run_tests(q, quiet=True), None
    finally:
        shutil.rmtree(q.rendu_dir, ignore_errors=True)


def main():
    if config.RENDU.exists():
        workspace.archive()
    print(ui.paint("graders must fail each of these broken answers", "bold"))
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda m: grade_mutant(m[0], m[1], m[3]), MUTANTS))
    shutil.rmtree(config.RENDU, ignore_errors=True)
    bad = 0
    for (rank_key, name, why, _), (result, problem) in zip(MUTANTS, results):
        if problem:
            bad += 1
            print(f"  {ui.paint('?', ui.HILITE)} {rank_key}/{name:<28} {problem}")
        elif result.passed:
            bad += 1
            print(f"  {ui.paint('✘', ui.ERR)} {rank_key}/{name:<28} PASSED but: {why}")
        else:
            print(f"  {ui.paint('✔', ui.OK)} {rank_key}/{name:<28} {ui.paint('caught: ' + why, ui.MUTED)}")
    print()
    print(f"{len(MUTANTS) - bad}/{len(MUTANTS)} broken answers caught")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
