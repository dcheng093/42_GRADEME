"""mini_db: starts your database server and talks to it with real
sockets."""

from __future__ import annotations

import os
import select
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # the harness imports this file: no import loop at runtime
    from examshell.native_harness import Checker, Context

TOTAL = 24
WAIT = 2.0


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def show(data: bytes | str) -> str:
    text = data.decode(errors="replace") if isinstance(data, bytes) else data
    text = text.replace("\n", "$\n")
    return text if len(text) < 300 else text[:300] + f"… ({len(text)} chars)"


class Client:
    def __init__(self, port: int) -> None:
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=WAIT)
        self.buf = b""

    def lines(self, count: int, timeout: float = WAIT) -> bytes:
        """Read `count` lines (or what came before the timeout)."""
        end = time.monotonic() + timeout
        while self.buf.count(b"\n") < count and time.monotonic() < end:
            self.sock.settimeout(max(0.01, end - time.monotonic()))
            try:
                chunk = self.sock.recv(1 << 20)
            except (socket.timeout, OSError):
                break
            if not chunk:
                break
            self.buf += chunk
        parts = self.buf.split(b"\n")
        taken = parts[:count]
        self.buf = b"\n".join(parts[count:])
        return (
            b"".join(p + b"\n" for p in taken)
            if len(parts) > count
            else b"\n".join(taken)
        )

    def ask(self, command: str) -> bytes:
        self.sock.sendall(command.encode() + b"\n")
        return self.lines(1)

    def close(self) -> None:
        self.sock.close()


class Server:
    def __init__(
        self, ctx: Context, binary: Path, port: int, path: Path
    ) -> None:
        self.ctx, self.port, self.path = ctx, port, path
        self.binary = binary
        self.grace = ctx.launch_grace(binary)
        self.proc = subprocess.Popen(
            [str(binary), str(port), str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

    def wait_ready(self) -> tuple[bool, bytes]:
        """(True once "ready\\n" came on stdout, what came)."""
        got = b""
        end = time.monotonic() + 3 + self.grace
        assert self.proc.stdout is not None  # stdout=PIPE
        fd = self.proc.stdout.fileno()
        while time.monotonic() < end and b"\n" not in got:
            ready, _, _ = select.select([fd], [], [], 0.1)
            if ready:
                chunk = os.read(fd, 64)
                if not chunk:
                    break
                got += chunk
        if got:
            self.ctx.launched(self.binary)
        return got.split(b"\n")[0] == b"ready", got

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait()


def run(ctx: Context, check: Checker) -> None:
    binary = ctx.user()
    port = free_port()
    save = ctx.tmp / "save.db"
    server = Server(ctx, binary, port, save)
    try:
        ok, got = server.wait_ready()
        check(
            f"./mini_db {port} save.db  prints 'ready' when it accepts"
            " connections",
            ok,
            [
                ("got", show(got)),
                ("hint", "print it (and flush: std::endl) after listen()"),
            ],
        )
        _first_run(check, server, port)
    finally:
        server.stop()

    server = Server(ctx, binary, port, save)
    try:
        ok, got = server.wait_ready()
        check(
            "restarted with the same file: 'ready' again",
            ok,
            [("got", show(got))],
        )
        _second_run(check, port)
    finally:
        server.stop()


def _ask(
    check: Checker,
    client: Client,
    command: str,
    expected: str,
    why: str | None = None,
) -> None:
    got = client.ask(command)
    rows: list[tuple[str, object]] = [
        ("expected", show(expected)),
        ("got", show(got)),
    ]
    if why:
        rows.append(("hint", why))
    check(
        command if len(command) < 80 else command[:77] + "…",
        got == expected.encode(),
        rows,
    )


def _first_run(check: Checker, server: Server, port: int) -> None:
    a = Client(port)
    _ask(check, a, "POST A B", "0\n")
    _ask(check, a, "POST B C", "0\n")
    _ask(check, a, "GET A", "0 B\n")
    _ask(check, a, "GET C", "1\n")
    _ask(check, a, "DELETE A", "0\n")
    _ask(check, a, "DELETE C", "1\n")
    _ask(check, a, "UNKNOWN_COMMAND", "2\n")
    _ask(
        check,
        a,
        "POST B D",
        "0\n",
        "POST on an existing key replaces its value",
    )
    _ask(check, a, "GET B", "0 D\n")

    b = Client(port)
    _ask(check, b, "GET B", "0 D\n", "every client shares the same database")
    b.close()
    time.sleep(0.1)
    _ask(
        check,
        a,
        "GET A",
        "1\n",
        "a client leaving must not disturb the others",
    )

    a.sock.sendall(b"POST x 1\nPOST y 2\nGET x\nGET y\n")
    got = a.lines(4)
    check(
        "4 commands in one send: 4 answers",
        got == b"0\n0\n0 1\n0 2\n",
        [("expected", show("0\n0\n0 1\n0 2\n")), ("got", show(got))],
    )

    a.sock.sendall(b"GE")
    time.sleep(0.2)
    a.sock.sendall(b"T x\n")
    got = a.lines(1)
    check(
        "'GE' then 'T x\\n' in two sends: one answer",
        got == b"0 1\n",
        [
            ("expected", show("0 1\n")),
            ("got", show(got)),
            ("hint", "keep the start of a command until its '\\n' arrives"),
        ],
    )

    key, value = "k" * 400, "v" * 500
    _ask(check, a, f"POST {key} {value}", "0\n")
    _ask(check, a, f"GET {key}", f"0 {value}\n")

    start = time.monotonic()
    n = 20000
    a.sock.sendall(
        "".join(f"POST key{i} value{i}\n" for i in range(n)).encode()
    )
    posted = a.lines(n, timeout=20)
    a.sock.sendall("".join(f"GET key{i}\n" for i in range(n)).encode())
    fetched = a.lines(n, timeout=20)
    took = time.monotonic() - start
    want = "".join(f"0 value{i}\n" for i in range(n)).encode()
    check(
        f"{n} POSTs then {n} GETs, sent all at once (be efficient)",
        posted == b"0\n" * n and fetched == want and took < 15,
        [
            ("took", f"{took:.1f}s"),
            (
                "got",
                (
                    f"{posted.count(b'0')} POST answers, "
                    f"{len(fetched.splitlines())} GET answers"
                ),
            ),
        ],
    )

    a.close()  # clients leave first, so the port is free again for the restart
    time.sleep(0.2)
    server.proc.send_signal(signal.SIGINT)
    try:
        server.proc.wait(timeout=3)
        stopped = True
    except subprocess.TimeoutExpired:
        stopped = False
    check(
        "SIGINT: the server saves and exits",
        stopped and server.path.is_file(),
        [
            ("exited", "yes" if stopped else "no, still running after 3s"),
            ("file", "written" if server.path.is_file() else "missing"),
        ],
    )


def _second_run(check: Checker, port: int) -> None:
    c = Client(port)
    _ask(
        check,
        c,
        "GET y",
        "0 2\n",
        "load the file given as argument when you start",
    )
    _ask(check, c, "GET B", "0 D\n")
    _ask(check, c, "GET A", "1\n", "deleted keys stay deleted")
    _ask(check, c, f"GET {'k' * 400}", f"0 {'v' * 500}\n")
    _ask(check, c, "GET key19999", "0 value19999\n")
    c.close()
