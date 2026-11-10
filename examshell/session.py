"""Practice mode and real exam mode."""

import math
import random
import sys
import time

from . import config, runner, ui, workspace
from .questions import Question, all_questions

PRACTICE_COMMANDS = (
    ("test", "grade your file"),
    ("next", "next question"),
    ("prev", "previous question"),
    ("sub", "redraw the subject"),
    ("solution", "peek at the reference solution"),
    ("retry", "detour to a question you failed before"),
    ("time", "time spent on this question"),
)
EXAM_COMMANDS = (
    ("test", "grade your file"),
    ("next", "swap for another question of this level (counts as a skip)"),
    ("sub", "redraw the subject"),
    ("time", "time left on the clock"),
)
LEAVE_COMMANDS = (
    ("help", "list every command"),
    ("menu", "back to the main menu"),
    ("exit", "quit GRADEME"),
)
PRACTICE_HELP = PRACTICE_COMMANDS + LEAVE_COMMANDS
EXAM_HELP = EXAM_COMMANDS + (
    ("help", "list every command"),
    ("menu", "give up and go back to the main menu"),
    ("exit", "give up and quit"),
)
FOOTER = "help · menu · exit"


# ── shared screen pieces ────────────────────────────────────────────────────
def _header(rank, mode_chip, right1="", left2="", right2=""):
    left1 = ui.chip(config.APP_NAME) + "  " + ui.paint(rank.title, "bold") + "  " + mode_chip
    print()
    print(ui.status_strip(left1, right1))
    if left2 or right2:
        print(ui.status_strip(left2, right2))
    print(" " + ui.rule())


def _level_label(rank, level):
    return ui.paint(f"L{level + 1}", ui.HILITE, "bold") + " " + ui.paint(rank.levels[level].theme, "bold")


def _solved_in_level(stats, rank, level):
    qs = [q for q in all_questions(rank) if q.level == level]
    return sum(1 for q in qs if stats.question(q.id).get("passes")), len(qs)


META = ("Assignment name", "Expected files", "Allowed functions", "Forbidden functions")


def _subject(q):
    lines, body_started = [], False
    for line in q.subject.splitlines():
        if line.strip() and set(line.strip()) == {"-"}:
            lines.append(ui.paint("┄" * (ui.card_width() - 4), ui.LINE))
            continue
        label = line.split(":", 1)[0].strip() if ":" in line else ""
        if not body_started and label in META:
            if label == "Assignment name":
                continue  # already the card title
            value = line.split(":", 1)[1].strip()
            lines.append(ui.paint(f"{label:<19}", ui.MUTED) + ui.paint(value, "bold"))
            continue
        if line.strip():
            body_started = True
        elif not body_started and lines and not lines[-1]:
            continue
        lines.append(line)
    while lines and not lines[-1].strip():
        lines.pop()
    rel = q.candidate.relative_to(config.ROOT)
    lines += ["", ui.paint(f"{'your file':<19}", ui.MUTED) + ui.paint(str(rel), ui.HILITE, "bold")]
    print()
    print(ui.card(lines, title=q.name, right=ui.paint(q.rank.levels[q.level].theme, ui.MUTED)))


def _commands(commands):
    print(ui.command_card(commands, footer=FOOTER))
    print()


def _help(commands):
    print(ui.command_card(commands, title="all commands"))


def _is_empty(q):
    return not q.candidate.is_file() or q.candidate.stat().st_size == 0


def _grade(q, stats, started):
    """Run the tests, print the verdict, record it. Returns the Result or None."""
    if _is_empty(q):
        ui.say(f"{q.candidate.relative_to(config.ROOT)} is empty — write your answer there first", ui.HILITE)
        return None
    print()
    print("  " + ui.paint("╭─ ", ui.LINE) + ui.paint("test results", ui.ACCENT, "bold"))
    result = runner.run_tests(q)
    print("  " + ui.paint("╰─", ui.LINE))
    stats.record_test(q.id, result.passed, time.monotonic() - started)
    print()
    print(ui.big("PASSED", ui.OK) if result.passed else ui.big("FAILED", ui.ERR))
    print()
    return result


def _show_solution(q):
    if q.solution is None:
        ui.say("no reference solution for this one")
        return
    lines = q.solution.read_text(errors="replace").rstrip().splitlines()
    print(ui.card([ui.paint(f"{i:>3} ", ui.MUTED) + line for i, line in enumerate(lines, 1)],
                  title=f"solution · {q.solution.name}", title_color=ui.HILITE, color=ui.HILITE))


def _ask(label):
    """Read a command. Ctrl-C means 'menu', Ctrl-D means 'exit'."""
    try:
        return ui.ask(label).lower()
    except KeyboardInterrupt:
        print()
        return "menu"
    except EOFError:
        print()
        return "exit"


# ── practice ────────────────────────────────────────────────────────────────
def level_run(rank, level):
    """Every question from `level` to the last level, each level shuffled."""
    playlist = []
    for li in range(level, len(rank.levels)):
        qs = [Question(rank, li, name) for name in rank.levels[li].pool]
        random.shuffle(qs)
        playlist += qs
    return playlist


def from_question(rank, index):
    """Start at all_questions(rank)[index] and walk the rest of the rank in order."""
    return all_questions(rank)[index:]


def _segment(playlist, idx):
    """(start, end) of the run of same-level questions around idx."""
    level = playlist[idx].level
    start = idx
    while start > 0 and playlist[start - 1].level == level:
        start -= 1
    end = idx
    while end + 1 < len(playlist) and playlist[end + 1].level == level:
        end += 1
    return start, end + 1


def practice(rank, playlist, stats):
    idx = 0
    solved = set()  # question ids passed during this run
    level_started = time.monotonic()
    detour = None  # a `retry` question, outside the playlist
    while True:
        start, end = _segment(playlist, idx)
        if detour:
            q, where = detour, ui.chip("RETRY", ui.HILITE)
        else:
            q = playlist[idx]
            where = ui.paint(f"question {idx - start + 1} of {end - start}", ui.MUTED)
        action = _practice_question(q, where, stats, solved, first=(idx == 0 and not detour))
        if detour:
            detour = None
            if isinstance(action, Question):
                detour = action
            elif action == "menu":
                return
            continue  # back to where the run was
        if action == "next":
            if idx + 1 == end:  # last question of this level
                nxt = playlist[end].level if end < len(playlist) else None
                go_on = _level_complete(rank, q.level, playlist[start:end], solved,
                                        time.monotonic() - level_started, nxt)
                if not go_on or nxt is None:
                    return
                level_started = time.monotonic()
            idx += 1
        elif action == "prev":
            idx -= 1
        elif isinstance(action, Question):
            detour = action
        else:  # menu
            return


def _practice_question(q, where, stats, solved, first):
    workspace.prepare(q)
    started = time.monotonic()
    redraw = True
    while True:
        if redraw:
            ui.clear()
            done, total = _solved_in_level(stats, q.rank, q.level)
            _header(q.rank, ui.chip("PRACTICE"), where, _level_label(q.rank, q.level), ui.level_bar(done, total))
            _subject(q)
            _commands(PRACTICE_COMMANDS)
            redraw = False
        cmd = _ask(q.name)
        if cmd == "test":
            result = _grade(q, stats, started)
            if result and result.passed:
                solved.add(q.id)
                ui.say(f"✔ solved in {ui.duration(time.monotonic() - started)}", ui.OK, "bold")
                try:
                    go = input(ui._rl_safe("  " + ui.paint("next question? [Y/n] ", ui.MUTED))).strip().lower()
                except (KeyboardInterrupt, EOFError):
                    go = "n"
                if go in ("", "y", "yes"):
                    return "next"
        elif cmd in ("next", "n"):
            return "next"
        elif cmd in ("prev", "p"):
            if first:
                ui.say("this is the first question of the run")
            else:
                return "prev"
        elif cmd in ("sub", "s", "clear"):
            redraw = True
        elif cmd in ("solution", "sol"):
            if ui.confirm("spoil the reference solution?"):
                _show_solution(q)
        elif cmd == "retry":
            failed = [n for n in stats.failed_questions(q.rank.key) if n != q.name]
            pool = [x for x in all_questions(q.rank) if x.name in failed]
            if not pool:
                ui.say("nothing to retry — no failed questions on record")
            else:
                return random.choice(pool)
        elif cmd in ("time", "t"):
            ui.say(f"on this question for {ui.duration(time.monotonic() - started)}", ui.ACCENT)
        elif cmd in ("help", "h", "?"):
            _help(PRACTICE_HELP)
        elif cmd in ("menu", "m", "back"):
            return "menu"
        elif cmd in ("exit", "quit", "q"):
            raise SystemExit(0)
        elif cmd:
            ui.say(f"unknown command '{cmd}' — type help", ui.ERR)


def _level_complete(rank, level, questions, solved, elapsed, next_level):
    """Congratulations screen between levels. Returns True to keep going."""
    done = [q for q in questions if q.id in solved]
    missed = [q for q in questions if q.id not in solved]
    ui.clear()
    print()
    if not missed:
        print(ui.big(f"L{level + 1} CLEAR", ui.OK))
        print()
        ui.say(f"congratulations — you solved every question in level {level + 1}!", ui.OK, "bold")
    else:
        print(ui.big(f"L{level + 1} DONE", ui.HILITE))
        print()
        ui.say(f"level {level + 1} finished — {len(done)} of {len(questions)} solved."
               + (" nice work!" if done else " the map remembers which ones you skipped."), ui.HILITE, "bold")
    print()
    lines = [
        ui.paint(f"{'level':<10}", ui.MUTED) + _level_label(rank, level),
        ui.paint(f"{'solved':<10}", ui.MUTED) + ui.level_bar(len(done), len(questions), 20),
        ui.paint(f"{'time':<10}", ui.MUTED) + ui.duration(elapsed),
    ]
    if missed:
        lines.append("")
        lines.append(ui.paint("not solved this run", ui.MUTED))
        lines += ["  " + ui.paint("✘ ", ui.ERR) + q.name for q in missed]
    if next_level is not None:
        lines += ["", ui.paint(f"{'next up':<10}", ui.MUTED) + _level_label(rank, next_level)
                  + ui.paint(f" · {len(rank.levels[next_level].pool)} questions, shuffled", ui.MUTED)]
    print(ui.card(lines, title=f"{rank.title} · level {level + 1} complete", color=ui.OK if not missed else ui.LINE))
    print()
    if next_level is None:
        print(ui.big("ALL DONE", ui.ACCENT))
        print()
        ui.say(f"that was the last level of {rank.title} — great run.", ui.ACCENT, "bold")
        print()
        try:
            ui.pause("press enter to go back to the menu")
        except (KeyboardInterrupt, EOFError):
            pass
        return False
    print(ui.command_card([("enter", f"continue to level {next_level + 1}"),
                           ("menu", "stop here and go back to the menu")], title="what next"))
    print()
    while True:
        cmd = _ask("continue")
        if cmd in ("", "c", "y", "yes", "next", "n", "continue"):
            return True
        if cmd in ("menu", "m", "back"):
            return False
        if cmd in ("exit", "quit", "q"):
            raise SystemExit(0)
        ui.say("press enter to continue, or type menu", ui.ERR)


# ── real exam ───────────────────────────────────────────────────────────────
class _ExamOver(Exception):
    def __init__(self, reason, quit_after=False):
        super().__init__(reason)
        self.reason, self.quit_after = reason, quit_after


def exam(rank, stats):
    n = len(rank.levels)
    ui.clear()
    print()
    print(ui.big(rank.title.replace(" ", "")))
    print()
    rules = [
        f"{n} levels · one random question per level · {ui.duration(rank.time_limit)} on the clock",
        f"each level cleared is worth {100 / n:.0f} points · grade {ui.paint('100', ui.OK, 'bold')} = all cleared",
        "a failed test keeps the same question"
        + (f", and adds a cooldown ({', '.join(f'{s}s' for s in config.COOLDOWN_STEPS)})"
           if config.COOLDOWN_ENABLED else ""),
        "`next` swaps the question for another from the same level",
        "no solutions, no retry — just like the real thing",
    ]
    print(ui.card([ui.paint("• ", ui.ACCENT) + r for r in rules], title=f"{rank.title} · real exam"))
    print()
    try:
        ui.pause("press enter to start the clock (ctrl-c to go back)")
    except (KeyboardInterrupt, EOFError):
        return

    workspace.archive()
    clock = {"start": time.monotonic()}
    clock["deadline"] = clock["start"] + rank.time_limit
    passed = 0
    quit_after = False
    reason = "finished"
    try:
        for level in range(n):
            _exam_level(rank, level, passed, clock, stats)
            passed += 1
    except _ExamOver as over:
        reason, quit_after = over.reason, over.quit_after

    elapsed = time.monotonic() - clock["start"]
    grade = round(passed * 100 / n)
    stats.record_exam(rank.key, grade, elapsed, passed, n)
    trace = workspace.archive()
    _exam_result(rank, grade, passed, elapsed, reason, trace)
    if quit_after:
        raise SystemExit(0)
    try:
        ui.pause("press enter to go back to the menu")
    except (KeyboardInterrupt, EOFError):
        pass


def _time_left(clock):
    return clock["deadline"] - time.monotonic()


def _exam_level(rank, level, passed, clock, stats):
    pool = list(rank.levels[level].pool)
    random.shuffle(pool)
    seen = [pool.pop()]
    q = Question(rank, level, seen[0])
    workspace.prepare(q)
    started = time.monotonic()
    fails = 0
    cooldown_until = 0.0
    redraw = True
    while True:
        if _time_left(clock) <= 0:
            raise _ExamOver("time")
        if redraw:
            ui.clear()
            left = _time_left(clock)
            clock_color = ui.ERR if left < 15 * 60 else ui.HILITE if left < 60 * 60 else ui.OK
            grade = round(passed * 100 / len(rank.levels))
            right = (ui.paint("grade ", ui.MUTED) + ui.paint(str(grade), "bold") + "   "
                     + ui.paint("◷ " + ui.duration(left), clock_color, "bold"))
            _header(rank, ui.chip("EXAM", ui.ERR), right, ui.roadmap(rank, level, passed), _level_label(rank, level))
            _subject(q)
            _commands(EXAM_COMMANDS)
            redraw = False

        cmd = _ask(ui.duration(_time_left(clock)))
        if _time_left(clock) <= 0:
            ui.say("time's up!", ui.ERR, "bold")
            raise _ExamOver("time")

        if cmd == "test":
            wait = cooldown_until - time.monotonic()
            if wait > 0 and not _countdown(cooldown_until):
                continue
            result = _grade(q, stats, started)
            if result is None:
                continue
            if result.passed:
                ui.say(f"✔ level {level + 1} cleared in {ui.duration(time.monotonic() - started)}"
                       f"  +{100 / len(rank.levels):.0f} points", ui.OK, "bold")
                if level + 1 < len(rank.levels):
                    try:
                        ui.pause("press enter for the next level")
                    except (KeyboardInterrupt, EOFError):
                        pass
                return
            fails += 1
            if config.COOLDOWN_ENABLED:
                steps = config.COOLDOWN_STEPS
                delay = steps[min(fails - 1, len(steps) - 1)]
                cooldown_until = time.monotonic() + delay
                if delay:
                    ui.say(f"next test available in {delay}s", ui.HILITE)
        elif cmd in ("next", "n"):
            if not pool:
                ui.say("no other question left in this level")
                continue
            seen.append(pool.pop())
            q = Question(rank, level, seen[-1])
            workspace.prepare(q)
            started = time.monotonic()
            redraw = True
        elif cmd in ("sub", "s", "clear"):
            redraw = True
        elif cmd in ("time", "t"):
            ui.say(f"{ui.duration(_time_left(clock))} left · "
                   f"{ui.duration(time.monotonic() - clock['start'])} elapsed", ui.ACCENT)
        elif cmd in ("help", "h", "?"):
            _help(EXAM_HELP)
        elif cmd in ("solution", "sol", "retry"):
            ui.say("not in the real exam ;)")
        elif cmd in ("menu", "m", "back"):
            if _safe_confirm("give up the exam?"):
                raise _ExamOver("abandoned")
        elif cmd in ("exit", "quit", "q"):
            if _safe_confirm("give up the exam and quit?"):
                raise _ExamOver("abandoned", quit_after=True)
        elif cmd:
            ui.say(f"unknown command '{cmd}' — type help", ui.ERR)


def _safe_confirm(question):
    try:
        return ui.confirm(question)
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def _countdown(until):
    """Live cooldown timer. Returns False if cancelled with ctrl-c."""
    try:
        while (left := until - time.monotonic()) > 0:
            sys.stdout.write("\r  " + ui.paint(f"◷ cooldown {math.ceil(left):>3}s", ui.HILITE)
                             + ui.paint("  (ctrl-c to cancel)", ui.MUTED) + "\x1b[K")
            sys.stdout.flush()
            time.sleep(0.2)
    except KeyboardInterrupt:
        print()
        return False
    sys.stdout.write("\r\x1b[K")
    return True


def _exam_result(rank, grade, passed, elapsed, reason, trace):
    ui.clear()
    color = ui.OK if grade == 100 else ui.HILITE if grade >= 50 else ui.ERR
    print()
    print(ui.big(f"{grade}/100", color))
    print()
    print("  " + ui.roadmap(rank, -1, passed))
    print()
    verdict = {
        "finished": "all levels cleared — go get that rank!",
        "time": "the clock ran out",
        "abandoned": "you gave up this one",
    }[reason]
    lines = [
        ui.paint(f"{'result':<10}", ui.MUTED) + verdict,
        ui.paint(f"{'levels':<10}", ui.MUTED) + ui.level_bar(passed, len(rank.levels), 20).replace("solved", "cleared"),
        ui.paint(f"{'time':<10}", ui.MUTED) + f"{ui.duration(elapsed)} of {ui.duration(rank.time_limit)}",
    ]
    if trace:
        lines.append(ui.paint(f"{'your code':<10}", ui.MUTED) + ui.paint(f"{trace.relative_to(config.ROOT)}/", ui.HILITE))
    print(ui.card(lines, title=f"{rank.title} · exam over", color=color))
    print()
