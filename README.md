```
    ██████  ██████      ████    ██████    ████████  ██      ██  ████████
  ██        ██    ██  ██    ██  ██    ██  ██        ████  ████  ██
  ██  ████  ██████    ████████  ██    ██  ██████    ██  ██  ██  ██████
  ██    ██  ██  ██    ██    ██  ██    ██  ██        ██      ██  ██
    ██████  ██    ██  ██    ██  ██████    ████████  ██      ██  ████████
```

**A terminal exam simulator for 42 — Rank 02 in C, Rank 03 in Python.**
Real levels, a ticking clock, cooldowns when you fail, and a grade out of 100. Or just practice at your own pace and peek at the solution when you're stuck.

No dependencies. Python 3.8+ and a terminal.

---

## Quick start

```bash
git clone https://github.com/dcheng093/42_examshell_python
cd 42_examshell_python
make
```

Write your answer in `rendu/<question>/`, then type `test`.

## Two ways to play

### Practice
Pick a rank, and you get a map of every level and question, with ✔ / ✘ next to the ones you've already tried. Type `L3` to work through **every** question of level 3 in a shuffled order (none skipped), or a number / name / `r` to start at that question, then do the rest of its level in a shuffled order. When you reach the end of a level you get a summary screen (solved count, time, anything you skipped) before moving on to the next level — or back to the menu.

### Real exam
One random question per level, a 3-hour clock, and a grade that goes up with each level you clear.

```
 GRADEME   Rank 03   EXAM                                  grade 17   ◷ 2:41:09
 ● L1 ━━ ◉ L2 ━━ ○ L3 ━━ ○ L4 ━━ ○ L5 ━━ ○ L6                          L2 parsing
 ──────────────────────────────────────────────────────────────────────────────────
```

- **Fail a test** and you keep the same question. Each fail adds a cooldown before the next `test`: 0s → 30s → 60s → 120s.
- **`next`** swaps your question for another one from the same level.
- **Run out of time** and the exam ends with whatever grade you have.
- No `solution`, no `retry`. Just like the real thing.
- It starts with an examshell login screen and uses an `examshell>` prompt. `status` prints the real status layout (assignment list with Success / Failure / Current, grade, end date, time remaining), and `grademe` asks "Are you sure?" first.
- Forbidden functions are checked from your source before any test runs.

## Commands

| command    | practice | exam | what it does                                   |
|------------|:--------:|:----:|------------------------------------------------|
| `grademe`  | ✔        | ✔    | run the tests on your rendu file (alias `test`) |
| `status`   |          | ✔    | examshell status: assignments, grade, end time |
| `finish`   |          | ✔    | end the exam with the grade you have           |
| `next`     | ✔        | ✔    | next question / swap for another in this level |
| `prev`     | ✔        |      | previous question                              |
| `sub [lang]` | ✔      | ✔    | show the subject again, e.g. `sub fr`          |
| `solution` | ✔        |      | peek at the reference solution                 |
| `retry`    | ✔        |      | detour to a random question you failed before  |
| `time`     | ✔        | ✔    | time on this question / time left              |
| `help`     | ✔        | ✔    | list the commands                              |
| `menu`     | ✔        | ✔    | back to the main menu (gives up in an exam)    |
| `exit`     | ✔        | ✔    | quit                                           |

`Ctrl-C` always takes you back to the menu.

## When a test fails

You don't get 100 lines of `PASS`. You get the first case that broke:

```
  ✘ check 5 failed  (4 passed before it)
  │ check     atoi('  -42abc')
  │ expected  -42
  │ got       42
```

If your code crashes, the card shows the exception and the exact line in your file. It also covers syntax errors, a missing function, a missing file, and an infinite loop (killed after 10s). Anything your code printed is shown underneath.

## Rank 03 levels

The current pool: 14 subjects, 6 levels, one assignment per level. It matches rank03.42exam.net and was imported by `scripts/import_rank03.py`.

| level | questions                                                                   |
|:-----:|-----------------------------------------------------------------------------|
| 1     | py_bracket_validator, py_cryptic_sorter *(no `sorted()` / `.sort()`)*       |
| 2     | py_echo_validator, py_mirror_matrix                                         |
| 3     | py_hidenp, py_inter, py_number_base_converter, py_pattern_tracker           |
| 4     | py_anagram, py_shadow_merge, py_string_permutation_checker                  |
| 5     | py_string_sculptor, py_twist_sequence                                       |
| 6     | py_whisper_cipher                                                           |

Careful: the file is `py_<name>.py`, but the function has no `py_` prefix (`def bracket_validator(...)`). Every subject is available in EN, DE, FR, ES, IT, RU, TR, ZH and AR (`sub fr`).

The **old pool** (alternate_case, atoi, rotate_90, …) is still there as **Rank 03 · old pool**, in practice mode only.

Rank 02 has the classic 4 levels (55 C exercises).

## Stats

Every `test` is recorded locally in `.examshell/stats.json` (gitignored). The **Stats** screen shows, for each question, a pass-rate bar, your best time, and a **weak** flag when you've failed it more often than you've passed it. It also lists your recent exam grades.

## Your code is never deleted

When you leave a session, `rendu/` is moved to `trace/<date>/`, so you can always go back and look at old attempts.

## Make targets

| target       | does                                                          |
|--------------|---------------------------------------------------------------|
| `make`       | start the shell                                               |
| `make check` | run every reference solution through its tester (should be 86/86) |
| `make clean` | delete `rendu/`, `trace/` and caches                          |

You can also grade a whole folder of your own answers at once:

```bash
python3 -m examshell --check rank02 --answers ~/my-rank02-answers
```

It finds `<question>/<file>` anywhere inside the folder.

## Adding a question

1. Create `subjects/rank03/<name>/` with:
   - `sub.txt`: the subject (keep the `Expected files :` line)
   - `solution.py`: a reference solution
   - `tests.py`: a `run(module, check)` function that calls `check(description, result, expected)` for each case
2. Add `<name>` to a level's pool in `examshell/config.py`.
3. Run `make check`.

For Rank 02, a question folder holds `sub.txt`, the reference `<name>.c`, a `main.c` for function exercises, and `cases.json`: a list of argv lists such as `[["zaz", "art", "zul"], []]`. Your program and the reference run on each list and their stdout must match. Your file is compiled with `-Wall -Wextra -Werror`.

## Layout

```
examshell/          the app (stdlib only)
  config.py         name, levels, timers, all in one place
  session.py        practice + exam flows
  harness.py        rank03 test harness + failure cards
  c_harness.py      rank02 test harness (compile once, run cases.json)
  runner.py         runs tests with a timeout
  ui.py             colours, block font, boxes, bars
  stats.py          local history
  workspace.py      rendu/ and trace/
subjects/
  rank02/levelN/<q>/   sub.txt, reference .c, main.c, cases.json
  rank03/<q>/          sub.txt, sub.<lang>.txt, solution.py, tests.py
  rank03_legacy/<q>/   the old rank03 pool
scripts/
  import_rank03.py     regenerate rank03 from an examshell_python checkout
```

## Requirements

- Python 3.8+
- For Rank 02: `gcc`
- Linux, macOS or WSL. Set `NO_COLOR=1` if you want plain output, or `ANIMATIONS = False` in `examshell/config.py` to keep the colours but skip the animations.

## Credits

The Rank 02 exercises and test cases come from [terminal-42s/42_examshell](https://github.com/terminal-42s/42_examshell). The Rank 03 subjects are adapted from [sergioromero2k/42_Exam_Ranks](https://github.com/sergioromero2k/42_Exam_Ranks), [this guy](https://note.com/it_morning/n/n070a3e238fe6?hl=en), [examshell-python](https://pypi.org/project/examshell-python/), [42exam.net](https://rank03.42exam.net/). The engine, the Python testers and everything else were rebuilt from scratch. 
