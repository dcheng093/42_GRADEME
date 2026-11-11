"""Building blocks for generated Python tests.py files.

A tests.py holds data (cases, computed with the reference solution) and calls
one of these from its run(module, check). They run inside the harness process.

`current` names the call being made, so a crash card can say what was
running.
"""

import copy
import random
import runpy
import signal
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from types import FrameType, ModuleType
from typing import Any, NoReturn, Protocol

# description of the call in progress (shown if it crashes)
current: str | None = None


class Check(Protocol):
    """The `check` callable a tests.py run() gets (harness.Checker)."""

    def __call__(
        self,
        description: str,
        result: object,
        expected: object = None,
        errors: list[str] | None = None,
    ) -> None:
        pass


# (method name, args): one call in a class test script
Op = tuple[str, tuple[Any, ...]]


def call_text(fname: str, args: Sequence[Any]) -> str:
    return f"{fname}({', '.join(map(repr, args))})"


def _unordered(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return sorted(value, key=repr)
    return value


def run_calls(
    module: ModuleType,
    check: Check,
    cases: Sequence[tuple[str, tuple[Any, ...], Any]],
    unordered: bool = False,
    no_mutation: bool = False,
) -> None:
    """cases: [(function name, args tuple, expected)]."""
    global current
    for fname, args, expected in cases:
        fn = getattr(module, fname)
        text = call_text(fname, args)
        given = copy.deepcopy(args)
        current = text
        got = fn(*given)
        current = None
        if unordered:
            check(
                text + "   (any order)", _unordered(got), _unordered(expected)
            )
        else:
            check(text, got, expected)
        if no_mutation:
            check(text + "  must not modify its input", given == args)


def run_roundtrip(
    module: ModuleType,
    check: Check,
    encode: str,
    decode: str,
    cases: Sequence[tuple[Any]],
) -> None:
    """decode(encode(x)) == x for every x, and encode returns a str."""
    global current
    enc, dec = getattr(module, encode), getattr(module, decode)
    for (value,) in cases:
        text = f"{decode}({encode}({value!r}))"
        current = f"{encode}({value!r})"
        packed = enc(copy.deepcopy(value))
        if not isinstance(packed, str):
            check(
                f"{encode}({value!r}) must return a str",
                type(packed).__name__,
                "str",
            )
        current = text
        got = dec(packed)
        current = None
        check(text, got, value)


SAME_ROOT = "__same_root__"  # pseudo-method: obj.find(a) == obj.find(b)


def _op_text(var: str, method: str, args: tuple[Any, ...]) -> str:
    if method == SAME_ROOT:
        a, b = args
        return f"{var}.find({a!r}) == {var}.find({b!r})"
    return f"{var}.{method}({', '.join(map(repr, args))})"


def apply_ops(obj: Any, ops: Sequence[Op]) -> list[Any]:
    """Run ops on obj, returning the list of results."""
    results = []
    for method, args in ops:
        if method == SAME_ROOT:
            results.append(obj.find(args[0]) == obj.find(args[1]))
        else:
            results.append(getattr(obj, method)(*copy.deepcopy(args)))
    return results


def run_class(
    module: ModuleType,
    check: Check,
    cls_name: str,
    var: str,
    cases: Sequence[tuple[tuple[Any, ...], Sequence[Op], Sequence[Any]]],
) -> None:
    """cases: [(constructor args, [(method, args)], [expected per op])].

    Every op's return value is compared; the failure shows the script up to
    the first wrong one, the way the subject writes its examples.
    """
    global current
    cls = getattr(module, cls_name)
    for ctor, ops, expected in cases:
        steps = [f"{var} = {cls_name}({', '.join(map(repr, ctor))})"]
        current = steps[0]
        obj = cls(*ctor)
        ok = True
        for (method, args), want in zip(ops, expected):
            steps.append(_op_text(var, method, args))
            current = "; ".join(steps)
            if method == SAME_ROOT:
                got = obj.find(args[0]) == obj.find(args[1])
            else:
                got = getattr(obj, method)(*copy.deepcopy(args))
            if got != want:
                current = None
                check(_short_script(steps), got, want)
                ok = False
                break
        current = None
        if ok:
            check(_short_script(steps), True)


def _short_script(steps: list[str], keep: int = 12) -> str:
    if len(steps) <= keep:
        return "; ".join(steps)
    hidden = len(steps) - keep
    return "; ".join(
        steps[:2] + [f"… {hidden} more calls …"] + steps[-(keep - 2):]
    )


# ── speed ───────────────────────────────────────────────────────────────────
class TooSlow(Exception):
    pass


def _alarm(_signum: int, _frame: FrameType | None) -> NoReturn:
    raise TooSlow()


def _timed(fn: Callable[[], Any], limit: float) -> tuple[Any, float]:
    """(result, seconds); raises TooSlow after `limit` seconds where SIGALRM
    exists."""
    use_alarm = hasattr(signal, "setitimer")
    if use_alarm:
        old = signal.signal(signal.SIGALRM, _alarm)
        signal.setitimer(signal.ITIMER_REAL, limit)
    start = time.perf_counter()
    try:
        result = fn()
    finally:
        if use_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)
    return result, time.perf_counter() - start


def run_perf(
    module: ModuleType,
    check: Check,
    tests_file: str,
    perf: Sequence[tuple[str, str, str, Callable[[random.Random], Any]]],
    slack: float = 10,
    floor: float = 1.5,
) -> None:
    """Big inputs: right answer, and not much slower than the reference.

    perf: [(description, kind, name, build)] where kind is "call" (build(rng)
    returns an args tuple for function `name`) or "class" (build(rng) returns
    (constructor args, ops) for class `name`).
    """
    global current
    ref = runpy.run_path(str(Path(tests_file).with_name("solution.py")))
    for description, kind, name, build in perf:
        args = build(random.Random(description))
        run_ref: Callable[[], Any]
        run_you: Callable[[], Any]
        if kind == "call":
            ref_fn, fn = ref[name], getattr(module, name)
            run_ref = lambda: ref_fn(*copy.deepcopy(args))  # noqa: E731
            run_you = lambda: fn(*copy.deepcopy(args))  # noqa: E731
        else:
            ctor, ops = args
            ref_cls, cls = ref[name], getattr(module, name)
            run_ref = lambda: apply_ops(ref_cls(*ctor), ops)  # noqa: E731
            run_you = lambda: apply_ops(cls(*ctor), ops)  # noqa: E731
        want, ref_time = _timed(run_ref, 60)
        limit = max(floor, slack * ref_time)
        current = description
        try:
            got, _ = _timed(run_you, limit)
        except TooSlow:
            current = None
            check(
                f"{description}: finish within {limit:.1f}s  (the reference"
                f" takes {ref_time:.2f}s)",
                False,
                errors=[
                    "too slow: probably a nested loop where the subject wants",
                    "something faster (see the complexity it asks for)",
                ],
            )
        current = None
        if got != want:
            check(
                f"{description}: right answer on a big input",
                False,
                errors=[f"expected {_brief(want)}", f"got      {_brief(got)}"],
            )
        else:
            check(f"{description}: fast enough", True)


def _brief(value: object, limit: int = 120) -> str:
    text = repr(value)
    return (
        text if len(text) <= limit else text[:limit] + f"… ({len(text)} chars)"
    )
