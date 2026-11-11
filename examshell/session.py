"""Practice mode and real exam mode."""

import math
import os
import random
import sys
import time
from datetime import datetime, timedelta

from . import config, runner, ui, workspace
from .questions import Question, all_questions

PRACTICE_COMMANDS = (
    ("test", "grade your file  (or grademe)"),
    ("next", "next question"),
    ("prev", "previous question"),
    ("sub", "redraw the subject  ·  sub fr / de / es / it / ru / tr / zh / ar"),
    ("solution", "peek at the reference solution"),
    ("retry", "detour to a question you failed before"),
    ("time", "time spent on this question"),
)
EXAM_COMMANDS = (
    ("grademe", "grade your file"),
    ("status", "assignments, grade and time left"),
    ("sub", "redraw the subject  ·  sub fr / de / es / it / ru / tr / zh / ar"),
    ("next", "swap for another question of this level (not in the real exam)"),
    ("finish", "end the exam with the grade you have"),
)
LEAVE_COMMANDS = (
    ("help", "list every command"),
    ("menu", "back to the main menu"),
    ("exit", "quit GRADEME"),
)
PRACTICE_HELP = PRACTICE_COMMANDS + LEAVE_COMMANDS
EXAM_HELP = EXAM_COMMANDS + (
    ("test", "same as grademe"),
    ("time", "time left on the clock"),
    ("help", "list every command"),
    ("menu", "same as finish, then back to the main menu"),
    ("exit", "same as finish, then quit"),
)
FOOTER = "help · menu · exit"
EXAM_FOOTER = "help · finish"
GRADE_WORDS = ("test", "grademe", "grade")
SUB_WORDS = ("sub", "s", "clear", "subject")


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


def _parse_sub(cmd, q):
    """'sub fr' -> 'fr'. Returns None (and says why) for an unknown language."""
    parts = cmd.split()
    if len(parts) == 1:
        return "en"
    lang = parts[1]
    if lang in q.languages:
        return lang
    have = " ".join(q.languages)
    ui.say(f"no '{lang}' subject for this one" + (f" — try: {have}" if len(q.languages) > 1 else ""), ui.ERR)
    return None


def _subject(q, lang="en"):
    lines, body_started = [], False
    for line in q.subject_in(lang).splitlines():
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
    right = q.rank.levels[q.level].theme + (f" · {lang}" if lang != "en" else "")
    print(ui.card(lines, title=q.name, right=ui.paint(right, ui.MUTED)))


def _commands(commands, footer=FOOTER):
    print(ui.command_card(commands, footer=footer))
    print()


def _help(commands):
    print(ui.command_card(commands, title="all commands"))


def _is_empty(q):
    if not q.candidate.is_file() or q.candidate.stat().st_size == 0:
        return True
    return workspace.is_stub(q.candidate.read_text(errors="replace"))


def _grade(q, stats, started):
    """Run the tests, print the verdict, record it. Returns the Result or None."""
    if _is_empty(q):
        ui.say(f"{q.candidate.relative_to(config.ROOT)} is empty — write your answer there first", ui.HILITE)
        return None
    print()
    print("  " + ui.paint("╭─ ", ui.LINE) + ui.paint("test results", ui.ACCENT, "bold"))
    result = runner.run_tests(q)
    print("  " + ui.paint("╰─", ui.LINE))
    before = dict(stats.question(q.id))
    stats.record_test(q.id, result.passed, time.monotonic() - started)
    print()
    if result.passed:
        ui.pass_banner()
        print()
        print("  " + _pass_note(before, stats.question(q.id)))
    else:
        ui.fail_banner()
    print()
    return result


def _pass_note(before, now):
    """One line under PASSED: first solve, a new best time, or the running tally."""
    best, old = now.get("best_time"), before.get("best_time")
    if not before.get("passes"):
        return ui.paint("✦ first solve", ui.HILITE, "bold") + ui.paint(f"  in {ui.duration(best)}", ui.MUTED)
    if old is not None and int(best) < int(old):
        return (ui.paint(f"✦ new best time {ui.duration(best)}", ui.HILITE, "bold")
                + ui.paint(f"  (was {ui.duration(old)})", ui.MUTED))
    return ui.paint(f"solved {now['passes']} times · best {ui.duration(best)}", ui.MUTED)


def _show_solution(q):
    if q.solution is None:
        ui.say("no reference solution for this one")
        return
    lines = q.solution.read_text(errors="replace").rstrip().splitlines()
    print(ui.card([ui.paint(f"{i:>3} ", ui.MUTED) + line for i, line in enumerate(lines, 1)],
                  title=f"solution · {q.solution.name}", title_color=ui.HILITE, color=ui.HILITE))


def _ask(label, symbol="❯"):
    """Read a command. Ctrl-C means 'menu', Ctrl-D means 'exit'."""
    try:
        return ui.ask(label, symbol=symbol).lower()
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
    """all_questions(rank)[index] first, then the rest of its level shuffled, then later levels."""
    picked = all_questions(rank)[index]
    rest = [Question(rank, picked.level, name) for name in rank.levels[picked.level].pool if name != picked.name]
    random.shuffle(rest)
    return [picked] + rest + level_run(rank, picked.level + 1)


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
    lang = "en"
    while True:
        if redraw:
            ui.clear()
            done, total = _solved_in_level(stats, q.rank, q.level)
            _header(q.rank, ui.chip("PRACTICE"), where, _level_label(q.rank, q.level), ui.level_bar(done, total))
            _subject(q, lang)
            _commands(PRACTICE_COMMANDS)
            redraw = False
        cmd = _ask(q.name)
        if cmd.split()[:1] and cmd.split()[0] in SUB_WORDS:
            picked = _parse_sub(cmd, q)
            if picked:
                lang, redraw = picked, True
            continue
        if cmd in GRADE_WORDS:
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
        ui.confetti(f"L{level + 1} CLEAR", ui.OK)
        print()
        ui.say(f"congratulations — you solved every question in level {level + 1}!", ui.OK, "bold")
    else:
        ui.reveal(f"L{level + 1} DONE", ui.HILITE)
        print()
        ui.say(f"level {level + 1} finished — {len(done)} of {len(questions)} solved."
               + (" nice work!" if done else " the map remembers which ones you skipped."), ui.HILITE, "bold")
    print()
    rest = []
    if missed:
        rest.append("")
        rest.append(ui.paint("not solved this run", ui.MUTED))
        rest += ["  " + ui.paint("✘ ", ui.ERR) + q.name for q in missed]
    if next_level is not None:
        rest += ["", ui.paint(f"{'next up':<10}", ui.MUTED) + _level_label(rank, next_level)
                 + ui.paint(f" · {len(rank.levels[next_level].pool)} questions, shuffled", ui.MUTED)]

    def summary(solved_so_far):  # the solved bar fills up
        return ui.card([
            ui.paint(f"{'level':<10}", ui.MUTED) + _level_label(rank, level),
            ui.paint(f"{'solved':<10}", ui.MUTED) + ui.level_bar(solved_so_far, len(questions), 20),
            ui.paint(f"{'time':<10}", ui.MUTED) + ui.duration(elapsed),
        ] + rest, title=f"{rank.title} · level {level + 1} complete", color=ui.OK if not missed else ui.LINE)

    ui.count_up(summary, 0, len(done), duration=0.6)
    print()
    if next_level is None:
        ui.confetti("ALL DONE", ui.ACCENT)
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


def _login():
    try:
        saved = config.EXAM_LOGIN_FILE.read_text().strip()
    except OSError:
        saved = ""
    return (saved or os.environ.get("GRADEME_LOGIN")
            or os.environ.get("USER") or os.environ.get("USERNAME") or "student")


def _boot(rank):
    """Fake examshell login + 'waiting for the exam to start'. False = backed out."""
    ui.clear()
    print()
    ui.reveal("examshell", ui.ACCENT)
    print()
    steps = [
        ("login: ", _login()),
        ("password: ", "********"),
        ("", "Connecting to exam server"),
    ]
    try:
        for label, value in steps:
            sys.stdout.write("  " + ui.paint(label, ui.MUTED))
            sys.stdout.flush()
            for ch in value:
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(0.03 if label else 0.0)
            if not label:
                for _ in range(6):
                    time.sleep(0.15)
                    sys.stdout.write(".")
                    sys.stdout.flush()
                sys.stdout.write(" " + ui.paint("OK", ui.OK, "bold"))
            print()
        time.sleep(0.2)
        n = len(rank.levels)
        print("  " + ui.paint(f"You are registered to the exam: {rank.title} ({rank.key}).", "bold"))
        print("  " + ui.paint(f"{n} levels · one assignment per level · {ui.duration(rank.time_limit)} · "
                              f"{_points(rank)} potential points each", ui.MUTED))
        print()
        rules = [
            "a failed grademe keeps the same assignment"
            + (f", with a cooldown ({', '.join(f'{s}s' for s in config.COOLDOWN_STEPS)})"
               if config.COOLDOWN_ENABLED else ""),
            "status shows your assignments, grade and time left",
            "sub fr / sub de / ... shows the subject in another language",
            "no solutions, no retry — just like the real thing",
        ]
        print(ui.card([ui.paint("• ", ui.ACCENT) + r for r in rules], title="before you start"))
        print()
        ui.pause("Waiting for the exam to start... press enter (ctrl-c to go back)")
    except (KeyboardInterrupt, EOFError):
        print()
        return False
    return True


def _points(rank):
    return round(100 / len(rank.levels))


def exam(rank, stats):
    if not _boot(rank):
        return

    n = len(rank.levels)
    workspace.archive()
    clock = {"start": time.monotonic(), "end_at": datetime.now() + timedelta(seconds=rank.time_limit)}
    clock["deadline"] = clock["start"] + rank.time_limit
    history = []  # [question name, "Success" | "Failure" | "Current" | "Skipped"], like examshell's list
    passed = 0
    quit_after = False
    reason = "finished"
    try:
        for level in range(n):
            _exam_level(rank, level, passed, clock, stats, history)
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


def _remaining_words(seconds):
    seconds = max(int(seconds), 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}hrs, {m}min and {s}sec"


def _status(rank, level, passed, clock, history, q):
    """The examshell `status` screen."""
    pts = _points(rank)
    grade = round(passed * 100 / len(rank.levels))
    marks = {"Success": ui.OK, "Failure": ui.ERR, "Current": ui.HILITE, "Skipped": ui.MUTED}
    lines = [
        f"You're connected as {ui.paint(_login(), 'bold')}.",
        ui.paint("You can log out at any time. If this program tells you you earned points,", ui.MUTED),
        ui.paint("then they will be counted whatever happens.", ui.MUTED),
        "",
        f"You are currently at level {ui.paint(str(level), 'bold')}.",
        "Assignments:",
    ]
    for i, (name, state) in enumerate(history):
        lines.append(f"  {i}: {ui.paint(name, 'bold')} for {pts} potential points "
                     f"({ui.paint(state, marks[state], 'bold')})")
    grade_color = ui.OK if grade == 100 else ui.HILITE if grade else ui.MUTED
    lines += [
        f"Grade: {ui.paint(f'{grade}/100', grade_color, 'bold')}",
        "",
        f"The end date for this exam is: {clock['end_at'].strftime('%d/%m/%Y %H:%M:%S')}",
        f"You have {ui.paint(_remaining_words(_time_left(clock)), 'bold')} remaining.",
        "",
        ui.paint(f"{'subject':<9}", ui.MUTED) + str(q.path.relative_to(config.ROOT)) + "/",
        ui.paint(f"{'rendu':<9}", ui.MUTED) + ui.paint(str(q.rendu_dir.relative_to(config.ROOT)) + "/", ui.HILITE, "bold"),
    ]
    print()
    print(ui.card(lines, title="status", right=ui.paint(rank.title, ui.MUTED)))
    print()


def _exam_level(rank, level, passed, clock, stats, history):
    pool = list(rank.levels[level].pool)
    random.shuffle(pool)
    seen = [pool.pop()]
    q = Question(rank, level, seen[0])
    history.append([q.name, "Current"])
    workspace.prepare(q)
    started = time.monotonic()
    fails = 0
    cooldown_until = 0.0
    redraw, show_status = True, True
    lang = "en"
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
            if show_status:  # examshell prints the status when you get a new assignment
                _status(rank, level, passed, clock, history, q)
                show_status = False
            _subject(q, lang)
            _commands(EXAM_COMMANDS, EXAM_FOOTER)
            redraw = False

        cmd = _ask("examshell", symbol=">")
        if _time_left(clock) <= 0:
            ui.say("time's up!", ui.ERR, "bold")
            raise _ExamOver("time")
        word = cmd.split()[0] if cmd.split() else ""

        if cmd in GRADE_WORDS:
            if not _safe_confirm("Are you sure you're ready to be graded?", default_yes=True):
                continue
            wait = cooldown_until - time.monotonic()
            if wait > 0 and not _countdown(cooldown_until):
                continue
            result = _grade(q, stats, started)
            if result is None:
                continue
            if result.passed:
                history[-1][1] = "Success"
                ui.say(f"✔ level {level + 1} cleared in {ui.duration(time.monotonic() - started)}"
                       f"  +{_points(rank)} points", ui.OK, "bold")
                if level + 1 < len(rank.levels):
                    try:
                        ui.pause("press enter for your next assignment")
                    except (KeyboardInterrupt, EOFError):
                        pass
                return
            history[-1][1] = "Failure"
            history.append([q.name, "Current"])
            fails += 1
            if config.COOLDOWN_ENABLED:
                steps = config.COOLDOWN_STEPS
                delay = steps[min(fails - 1, len(steps) - 1)]
                cooldown_until = time.monotonic() + delay
                if delay:
                    ui.say(f"next grademe available in {delay}s", ui.HILITE)
        elif word in SUB_WORDS:
            picked = _parse_sub(cmd, q)
            if picked:
                lang, redraw = picked, True
        elif cmd in ("status", "st"):
            _status(rank, level, passed, clock, history, q)
        elif cmd in ("next", "n"):
            if not pool:
                ui.say("no other assignment left in this level")
                continue
            history[-1][1] = "Skipped"
            seen.append(pool.pop())
            q = Question(rank, level, seen[-1])
            history.append([q.name, "Current"])
            workspace.prepare(q)
            started = time.monotonic()
            fails, cooldown_until = 0, 0.0
            redraw, show_status, lang = True, True, "en"
        elif cmd in ("time", "t"):
            ui.say(f"You have {_remaining_words(_time_left(clock))} remaining · "
                   f"{ui.duration(time.monotonic() - clock['start'])} elapsed", ui.ACCENT)
        elif cmd in ("help", "h", "?"):
            _help(EXAM_HELP)
        elif cmd in ("solution", "sol", "retry"):
            ui.say("not in the real exam ;)")
        elif cmd in ("finish", "menu", "m", "back"):
            if _safe_confirm("Do you really want to end the exam? Your grade will be final."):
                raise _ExamOver("finished_early")
        elif cmd in ("exit", "quit", "q", "logout"):
            if _safe_confirm("End the exam and quit?"):
                raise _ExamOver("finished_early", quit_after=True)
        elif cmd:
            ui.say(f"{cmd}: command not found — type help", ui.ERR)


def _safe_confirm(question, default_yes=False):
    try:
        return ui.confirm(question, default_yes=default_yes)
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

    def tint(g):
        return ui.OK if g == 100 else ui.HILITE if g >= 50 else ui.ERR

    color = tint(grade)
    print()
    ui.count_up(lambda g: ui.big(f"{g}/100", tint(g)), 0, grade, duration=0.9)
    print()
    ui.play([("  " + ui.roadmap(rank, -1, k), 0.15) for k in range(passed + 1)])
    print()
    verdict = {
        "finished": "all levels cleared — go get that rank!",
        "time": "the clock ran out",
        "abandoned": "you gave up this one",
        "finished_early": "you ended the exam",
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
