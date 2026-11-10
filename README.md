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
Pick a rank, and you get a map of every level and question, with ✔ / ✘ next to the ones you've already tried. Type `L3` to work through **every** question of level 3 in a shuffled order (none skipped), or a number / name / `r` to start at one question and go in order. When you reach the end of a level you get a summary screen (solved count, time, anything you skipped) before moving on to the next level — or back to the menu.

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

## Commands

| command    | practice | exam | what it does                                   |
|------------|:--------:|:----:|------------------------------------------------|
| `test`     | ✔        | ✔    | run the tests on your rendu file               |
| `next`     | ✔        | ✔    | next question / swap for another in this level |
| `prev`     | ✔        |      | previous question                              |
| `sub`      | ✔        | ✔    | show the subject again                         |
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

The real exam has 6 levels, each with its own pool of questions, and you get one question per level. This is my best guess at the grouping, by difficulty:

| level | theme              | questions                                             |
|:-----:|--------------------|-------------------------------------------------------|
| 1     | strings            | alternate_case, capitalize_words, valid_anagram       |
| 2     | parsing            | atoi, py_echo_validator, whisper_lipher               |
| 3     | sorting            | sorted, merge_and_sort_desc, customSortString         |
| 4     | counting & hashing | twoSum, topKFrequent, py_pattern_tracker              |
| 5     | matrices           | mirror_matrix, mirror_matrix_vertical, rotate_90      |
| 6     | algorithms         | brackets, convert_base                                |

If you know the real pools, just edit `examshell/config.py`. That one file is the only place they're defined.

Rank 02 has the classic 4 levels (55 C exercises).

## Stats

Every `test` is recorded locally in `.examshell/stats.json` (gitignored). The **Stats** screen shows, for each question, a pass-rate bar, your best time, and a **weak** flag when you've failed it more often than you've passed it. It also lists your recent exam grades.

## Your code is never deleted

When you leave a session, `rendu/` is moved to `trace/<date>/`, so you can always go back and look at old attempts.

## Make targets

| target       | does                                                          |
|--------------|---------------------------------------------------------------|
| `make`       | start the shell                                               |
| `make check` | run every reference solution through its tester (should be 72/72) |
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

## Layout

```
examshell/          the app (stdlib only)
  config.py         name, levels, timers, all in one place
  session.py        practice + exam flows
  harness.py        rank03 test harness + failure cards
  runner.py         runs tests with a timeout
  ui.py             colours, block font, boxes, bars
  stats.py          local history
  workspace.py      rendu/ and trace/
subjects/
  rank02/levelN/<q>/   sub.txt, reference .c, tester.sh
  rank03/<q>/          sub.txt, solution.py, tests.py
```

## Requirements

- Python 3.8+
- For Rank 02: `bash` and `gcc`
- Linux, macOS or WSL. Set `NO_COLOR=1` if you want plain output.

## Credits

The Rank 02 exercises and testers come from [terminal-42s/42_examshell](https://github.com/terminal-42s/42_examshell). The Rank 03 subjects are adapted from [sergioromero2k/42_Exam_Ranks](https://github.com/sergioromero2k/42_Exam_Ranks). The engine, the Python testers and everything else were rebuilt from scratch.
