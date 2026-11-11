```
    ██████  ██████      ████    ██████    ████████  ██      ██  ████████
  ██        ██    ██  ██    ██  ██    ██  ██        ████  ████  ██
  ██  ████  ██████    ████████  ██    ██  ██████    ██  ██  ██  ██████
  ██    ██  ██  ██    ██    ██  ██    ██  ██        ██      ██  ██
    ██████  ██    ██  ██    ██  ██████    ████████  ██      ██  ████████
```

**The all-in-one 42 examshell: every exam rank, in C, C++ and Python, on the Python cursus and the C cursus.**
It has real levels, a ticking clock, cooldowns when you fail, and a grade out of 100. Or practise at your own pace and peek at the solution when you're stuck.

Other examshells check that your output matches. This one also grades the way an examiner would:
- hidden test mains and edge cases, not just the subject's examples
- valgrind for leaks, invalid accesses and open fds
- fd and zombie checks for the process exercises, and real sockets for the servers
- speed checks where a subject asks for a complexity
- a verdict your program can't fake by printing "PASSED"

`make selftest` proves the graders fail 20 deliberately broken answers.

The shell has no dependencies: Python 3.10+, a terminal, and `gcc`/`c++` for the C and C++ ranks. `valgrind` is optional and adds leak checks.

---

## Quick start

```bash
git clone https://github.com/dcheng093/42_examshell_python
cd 42_examshell_python
make
```

Write your answer in `rendu/<question>/`, then type `test`.

## What's inside

### Python cursus

This is 42's current curriculum: Rank 02 is in C, and ranks 03 to 06 are in Python. The pools match [42exam.net](https://42exam.net/).

| rank | levels | questions |
|------|--------|-----------|
| **Rank 02** (C) | 4 | 55, plus `ft_strpbrk` and `ft_strspn` as practice-only extras *(rare: never drawn in an exam)* |
| **Rank 03** | 6 | L1 py_bracket_validator, py_cryptic_sorter · L2 py_echo_validator, py_mirror_matrix · L3 py_hidenp, py_inter, py_number_base_converter, py_pattern_tracker · L4 py_anagram, py_shadow_merge, py_string_permutation_checker · L5 py_string_sculptor, py_twist_sequence · L6 py_whisper_cipher |
| **Rank 04** | 4 | L1 py_array_rotation_detector, py_constellation_mapper · L2 py_list_intersection_finder, py_merge_sorted_lists · L3 py_palindrome_partitioner, py_package_dependency_resolver · L4 py_sliding_window_maximum |
| **Rank 05** | 3 | L1 py_compress_decompress, py_spiral_matrix, py_room_scheduler · L2 py_graph_cycle_detector, py_island_matrix_counter · L3 py_prism_detector, py_word_ladder |
| **Rank 06** | 2 | L1 prefix_dictionary, pack_strings, task_order, redundant_link, trie_autocomplete · L2 union_find_system, cache_keeper, min_heap, bridge_finder |
| **Rank 03 · Python beta pool** | 6 | the first Python pool (alternate_case, atoi, rotate_90, …), practice only |

Watch the names in the Python ranks. The file is `py_<name>.py`, but the function usually has no `py_` prefix (`def bracket_validator(...)`), except where the subject's signature says otherwise (`py_graph_cycle_detector`). Every Python subject is available in EN, DE, FR, ES, IT, RU, TR, ZH and AR (`sub fr`). Rank 06 asks for classes too; your file then starts with the class skeleton already written.

### C cursus

These are the exams from before the switch to Python: C, then C++ in rank 05.

| rank | levels | questions |
|------|--------|-----------|
| **Rank 03** (C) | 2 | L1 broken_gnl, filter, scanf · L2 n_queens, permutations, powerset, rip, tsp |
| **Rank 04** (C) | 2 | L1 ft_popen, picoshell, sandbox · L2 argo, vbc |
| **Rank 05** (C++ / C) | 2 | L1 bigint, polyset, vect2 (C++98) · L2 bsq, life |
| **Rank 06** (C / C++) | 1 | mini_serv, mini_db |

When a subject hands out files, they are copied to `rendu/<question>/`: the tsp and scanf skeletons, the broken get_next_line, the argo and vbc starters, polyset's bag classes, and the subject `main.cpp`. Polyset's bag classes are only for reading. The tests always compile the originals, so editing your copy changes nothing.

## Two ways to play

### Practice
Pick a rank and you get a map of every level and question, with ✔ / ✘ next to the ones you've already tried.
- Type `L3` to work through **every** question of level 3 in a shuffled order, with none skipped.
- Type a number, a name or `r` to start at that question, then do the rest of its level in a shuffled order.

When you reach the end of a level you get a summary screen (solved count, time, anything you skipped). From there you move on to the next level, or go back to the menu.

### Real exam
You get one random question per level, a 3-hour clock, and a grade that goes up with each level you clear.

```
 GRADEME   Rank 03   EXAM                                  grade 17   ◷ 2:41:09
 ● L1 ━━ ◉ L2 ━━ ○ L3 ━━ ○ L4 ━━ ○ L5 ━━ ○ L6                          L2 parsing
 ──────────────────────────────────────────────────────────────────────────────────
```

- **Fail a test** and you keep the same question. Each fail adds a cooldown before the next `test`: 0s → 30s → 60s → 120s.
- **`next`** swaps your question for another one from the same level.
- **Run out of time** and the exam ends with whatever grade you have.
- There's no `solution` and no `retry`, just like the real thing.
- It starts with an examshell login screen and uses an `examshell>` prompt.
  - `status` prints the real status layout: the assignment list with Success / Failure / Current, the grade, the end date and the time remaining.
  - `grademe` asks "Are you sure?" first.

## Commands

| command    | practice | exam | what it does                                   |
|------------|:--------:|:----:|------------------------------------------------|
| `grademe`  | ✔        | ✔    | run the tests on your rendu files (alias `test`) |
| `status`   |          | ✔    | examshell status: assignments, grade, end time |
| `finish`   |          | ✔    | end the exam with the grade you have           |
| `next`     | ✔        | ✔    | next question / swap for another in this level |
| `prev`     | ✔        |      | previous question                              |
| `sub [lang]` | ✔      | ✔    | show the subject again, e.g. `sub fr`          |
| `solution` | ✔        |      | peek at the reference solution (every file)    |
| `retry`    | ✔        |      | detour to a random question you failed before  |
| `time`     | ✔        | ✔    | time on this question / time left              |
| `help`     | ✔        | ✔    | list the commands                              |
| `menu`     | ✔        | ✔    | back to the main menu (gives up in an exam)    |
| `exit`     | ✔        | ✔    | quit                                           |

`Ctrl-C` always takes you back to the menu.

## How you're graded

**Python.** Your function is called on the subject's examples, on hand-picked edge cases, and on seeded random cases. The expected values come from a reference solution.
- Forbidden functions and modules (`sorted()`, `heapq`, `collections.OrderedDict`, …) are found in your source before anything runs, even through aliases.
- Some subjects ask for a complexity: sliding_window_maximum, merge_sorted_lists, palindrome_partitioner, cache_keeper, min_heap and union_find. Those also get a big input, and you must finish within 10× the reference's time.
- Class subjects are replayed as scripts, the way the examples show them (`h = MinHeap(); h.push(5); h.pop()`).
- Some subjects don't fix every detail, such as an order of results, or two readings of the same rule. Those cases are compared without order, or left out, so a reasonable answer never fails on something the subject doesn't say.

**C and C++.** Your files are compiled with the exam flags: `-Wall -Wextra -Werror`, plus `-std=c++98` for the C++ classes. Then they run next to a reference, on hidden test mains and inputs: argv, stdin, files and several `BUFFER_SIZE` values.
- When the output is right, a sample of runs goes through **valgrind**. It reports definite and indirect leaks, invalid reads and writes, bad frees, and fds left open, with the file and line in your code. Without valgrind (macOS, or not installed) this step is skipped with a warning.
- filter is also run with a `read()` that returns 1 to 7 bytes at a time, like the exam's "random buffer sizes".
- ft_popen, picoshell and sandbox are checked for fds left open (in your process and in the command) and for children never waited for. They also get pipelines that hang if a pipe end stays open, and functions that crash, loop or ignore `SIGALRM`.
- **mini_serv** and **mini_db** are started and driven with real sockets:
  - exact messages and partial lines
  - ids that aren't reused
  - a client that never reads, while 6 MB must still reach the others
  - fd counts after clients leave
  - `SIGINT` save and reload, and a 20 000-command speed run

The verdict comes from the harness itself, never from what your program prints, so printing "checks passed" gets you nothing.

It's quick:
- The reference's results are cached in `.examshell/refcache/`, so a test only builds and runs your code.
- Builds and cases run in parallel. The report still shows the first failing case in order.
- A `test` usually takes about a second; the slowest, mini_serv, takes about 3s.

## When a test fails

You don't get 100 lines of `PASS`. You get the first case that broke:

```
  ✘ check 5 failed  (4 passed before it)
  │ check     atoi('  -42abc')
  │ expected  -42
  │ got       42
```

```
  ✘ wrong output  (case 4 of 19, 3 passed before it)
  │ run       echo 'dxss' | ./life 3 3 1
  │ expected     $
  │           OOO$
  │              $
  │ got          $
  │           O O$
  │              $
```

```
  ✘ memory leak  (output was right, case 2)
  │ test      addition, ++, copies
  │ lost      16 bytes in 1 block (definitely lost)
  │ allocated bigint.cpp line 4  (bigint::bigint())
```

Other failures get cards too:
- compile errors (the line, the code, the message)
- crashes (the signal, or the exception and its line)
- a missing function or file
- timeouts and slow solutions

Anything your Python code printed is shown underneath.

## Stats

Every `test` is recorded locally in `.examshell/stats.json` (gitignored). The **Stats** screen shows these for each question you've tried:
- a pass-rate bar
- your best time
- a **weak** flag when you've failed it more often than you've passed it

It also lists your recent exam grades.

## Your code is never deleted

When you leave a session, `rendu/` is moved to `trace/<date>/`, so you can always go back and look at old attempts. Untouched starters and handed-out files don't count.

## Make targets

| target              | does                                                                |
|---------------------|---------------------------------------------------------------------|
| `make`              | start the shell                                                     |
| `make check`        | run every reference solution through its tester (131/131, ~10s)     |
| `make check-python` | the same for the Python cursus only                                 |
| `make check-c`      | the same for the C cursus only                                      |
| `make selftest`     | feed the graders 20 broken answers: every one must fail             |
| `make clean`        | delete `rendu/`, `trace/` and caches                                |

You can also grade a whole folder of your own answers at once:

```bash
python3 -m examshell --check rank02 --answers ~/my-rank02-answers
```

It finds `<question>/<file>` anywhere inside the folder. `--check` takes a rank key (`rank04`, `old_rank05`, …), `python`, `c` or `all`.

## Adding or updating questions

**Python ranks (03–06).** Subjects come from snapshots of 42exam.net in `scripts/data/`.
1. `python3 scripts/fetch_42exam.py` refreshes the snapshots. It never runs the site's JavaScript.
2. Write or fix `subjects/rankNN/<name>/solution.py` by hand.
3. `python3 scripts/import_python.py [3 4 5 6]` writes `sub*.txt`, `tests.py` and `starter.py`. The import stops if your solution disagrees with a published example.
4. Edge cases, random generators, ambiguous readings and speed checks live in `scripts/python_cases.py`.

**C / C++ questions.** A question folder holds:
- `sub.txt` (keep the `Expected files :` line; `*.c *.h` works)
- `ref/` with the reference
- optional `given/`, compiled from there, and `handout/`, copied to rendu
- `mains/` for the hidden test mains
- a `spec.json`

```json
{
  "compiler": "c++", "std": "c++98", "leaks": true, "fds": false,
  "builds": [
    {"name": "the subject's main", "main": "mains/subject.cpp", "cases": [[]]},
    {"name": "BUFFER_SIZE=1", "main": "mains/read.c", "defines": ["BUFFER_SIZE=1"],
     "cases": [{"argv": ["f"], "files": {"f": "a\nb"}}, {"stdin": "x\n", "compare": ["stdout", "exit"]}]}
  ]
}
```

Comparisons are `stdout`, `stdout_unordered`, `stdout_numbers` (±0.01), `exit` and `stderr`. Rank 02 folders keep their simple form: a reference `<name>.c`, an optional `main.c`, and `cases.json` as a list of argv lists.

For anything that isn't "run and compare" (servers, timing), a `tester.py` with `run(ctx, check)` takes over. See `examshell/native_harness.py` for `ctx`.

After any change, run `make check` and `make selftest`.

## Layout

```
examshell/            the app (stdlib only)
  config.py           ranks, levels, timers, all in one place
  session.py          practice + exam flows
  harness.py          Python test harness + failure cards
  pytests.py          call / class / round-trip / speed checks for tests.py
  native_harness.py   C / C++ harness: builds, cases, valgrind, tester.py
  runner.py           runs a harness with a timeout, reads its verdict
  questions.py        a question's files, subject, reference
  ui.py · stats.py · workspace.py
subjects/
  rank02/levelN/<q>/        sub.txt, <q>.c, main.c, cases.json
  rank03..06/<q>/           sub*.txt, solution.py, tests.py, starter.py
  old_rank03..06/<q>/       the C cursus: sub.txt, spec.json, ref/, mains/, given/, handout/, tester.py
  rank03_legacy/<q>/        the Python beta pool
scripts/
  fetch_42exam.py · import_python.py · python_cases.py · selftest.py · data/
```

## Requirements

- Python 3.10+.
- For C and C++: `gcc` (or `cc`/`clang`) and `c++`.
- `valgrind` is optional. It adds the leak, memory-error and fd checks (Linux).
- Linux, WSL or macOS. ft_popen, picoshell, filter's short reads and the server testers rely on `/proc` and `LD_PRELOAD`, so they are fully checked on Linux and WSL.
- Set `NO_COLOR=1` for plain output, or `ANIMATIONS = False` in `examshell/config.py` to keep the colours but skip the animations.

## Credits

See [CREDITS.md](CREDITS.md):
- the Rank 02 exercises and cases are from [terminal-42s/42_examshell](https://github.com/terminal-42s/42_examshell)
- the Python ranks are from [42exam.net](https://42exam.net/) and [examshell-python](https://pypi.org/project/examshell-python/)
- the old Python pool is adapted from [sergioromero2k/42_Exam_Ranks](https://github.com/sergioromero2k/42_Exam_Ranks) and [this post](https://note.com/it_morning/n/n070a3e238fe6?hl=en)
- the C cursus subjects are 42's

The engine, the C cursus references, tests and testers, and the Python ranks' reference solutions and tests were written for GRADEME.
