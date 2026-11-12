"""mini_serv: starts your server and talks to it with real sockets."""

from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # the harness imports this file: no import loop at runtime
    from examshell.native_harness import Checker, Context

TOTAL = 15
WAIT = 2.0  # seconds to wait for a message that should come
QUIET = 0.2  # seconds of silence that count as "nothing was sent"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def show(data: bytes) -> str:
    text = data.decode(errors="replace").replace("\n", "$\n")
    return text if text else "(nothing)"


class Client:
    def __init__(self, port: int, rcvbuf: int | None = None) -> None:
        self.sock = socket.socket()
        if rcvbuf:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
        self.sock.settimeout(WAIT)
        self.sock.connect(("127.0.0.1", port))
        self.buf = b""

    def send(self, data: bytes) -> None:
        self.sock.sendall(data)

    def read_for(self, seconds: float, want: int | None = None) -> bytes:
        """Collect what arrives for `seconds` (or until `want` bytes are
        there)."""
        end = time.monotonic() + seconds
        while time.monotonic() < end and (
            want is None or len(self.buf) < want
        ):
            self.sock.settimeout(max(0.01, end - time.monotonic()))
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                break
            except OSError:
                break
            if not chunk:
                break
            self.buf += chunk
        data, self.buf = self.buf, b""
        return data

    def expect(self, expected: bytes) -> tuple[bool, bytes]:
        """(ok, got): waits for len(expected) bytes, then a moment for
        extras."""
        got = self.read_for(WAIT, len(expected))
        got += self.read_for(0.05)
        return got == expected, got

    def close(self) -> None:
        self.sock.close()


def run(ctx: Context, check: Checker) -> None:
    source = ctx.builder.user_dir / "mini_serv.c"
    binary = ctx.user()
    defines = [
        line
        for line in source.read_text(errors="replace").splitlines()
        if line.lstrip().startswith("#define")
    ]
    check(
        "no #define in mini_serv.c",
        not defines,
        [("found", "\n".join(defines[:3]))],
    )

    proc = subprocess.run([str(binary)], capture_output=True, timeout=5)
    check(
        "./mini_serv  (no argument)  -> 'Wrong number of arguments' on stderr,"
        " exit 1",
        proc.stderr == b"Wrong number of arguments\n" and proc.returncode == 1,
        [
            ("expected", "stderr: Wrong number of arguments$   exit 1"),
            ("got", f"stderr: {show(proc.stderr)}   exit {proc.returncode}"),
        ],
    )

    busy = socket.socket()
    busy.bind(("127.0.0.1", 0))
    busy.listen(1)
    try:
        proc = subprocess.run(
            [str(binary), str(busy.getsockname()[1])],
            capture_output=True,
            timeout=3,
        )
        out: bytes = proc.stderr
        code: int | None = proc.returncode
    except subprocess.TimeoutExpired:
        out, code = b"(still running)", None
    busy.close()
    check(
        "./mini_serv <a port already in use>  -> 'Fatal error' on stderr,"
        " exit 1",
        out == b"Fatal error\n" and code == 1,
        [
            ("expected", "stderr: Fatal error$   exit 1"),
            ("got", f"stderr: {show(out)}   exit {code}"),
        ],
    )

    port = free_port()
    server = subprocess.Popen(
        [str(binary), str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _session(ctx, check, server, port)
    finally:
        server.kill()
        server.wait()


def _wait_listening(server: subprocess.Popen[bytes], port: int) -> bool:
    end = time.monotonic() + 3
    while time.monotonic() < end:
        if server.poll() is not None:
            return False
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return True
        except OSError:
            time.sleep(0.05)
    return False


def _fd_count(pid: int) -> int | None:
    try:
        return len(os.listdir(f"/proc/{pid}/fd"))
    except OSError:
        return None


def _session(
    ctx: Context, check: Checker, server: subprocess.Popen[bytes], port: int
) -> None:
    if not _wait_listening(server, port):
        ctx.fail(
            "the server doesn't accept connections",
            [
                ("run", f"./mini_serv {port}"),
                ("hint", "bind 127.0.0.1, listen, then select() + accept()"),
            ],
        )
    # the probe connection above was client 0: it arrived and left
    time.sleep(0.2)
    baseline = _fd_count(server.pid)

    c1 = Client(port)
    check(
        "a client alone receives nothing about itself",
        c1.read_for(QUIET) == b"",
    )

    c2 = Client(port)
    ok, got = c1.expect(b"server: client 2 just arrived\n")
    check(
        "client 2 connects: the others get 'server: client 2 just arrived' "
        " (ids keep counting: 0 was a probe)",
        ok,
        [
            ("expected", show(b"server: client 2 just arrived\n")),
            ("got", show(got)),
        ],
    )

    c1.send(b"hello\n")
    ok, got = c2.expect(b"client 1: hello\n")
    quiet = c1.read_for(QUIET)
    check(
        "client 1 sends 'hello\\n': the others get 'client 1: hello'",
        ok,
        [("expected", show(b"client 1: hello\n")), ("got", show(got))],
    )
    check(
        "the sender doesn't get its own message back",
        quiet == b"",
        [("got", show(quiet))],
    )

    c2.send(b"a\nb\nc\n")
    ok, got = c1.expect(b"client 2: a\nclient 2: b\nclient 2: c\n")
    check(
        "one message with 3 lines: 'client 2: ' before every line",
        ok,
        [
            ("expected", show(b"client 2: a\nclient 2: b\nclient 2: c\n")),
            ("got", show(got)),
        ],
    )

    c1.send(b"par")
    early = c2.read_for(QUIET)
    c1.send(b"tial\n")
    ok, got = c2.expect(b"client 1: partial\n")
    check(
        "'par' then 'tial\\n' in two sends: one line 'client 1: partial'",
        early == b"" and ok,
        [
            ("expected", show(b"client 1: partial\n")),
            ("got", show(early + got)),
            (
                "hint",
                (
                    "keep what comes after the last \\n until the rest of the"
                    " line arrives"
                ),
            ),
        ],
    )

    c3 = Client(port)
    ok1, got1 = c1.expect(b"server: client 3 just arrived\n")
    ok2, got2 = c2.expect(b"server: client 3 just arrived\n")
    check(
        "client 3 connects: every other client is told",
        ok1 and ok2,
        [("client 1 got", show(got1)), ("client 2 got", show(got2))],
    )

    c2.close()
    ok1, got1 = c1.expect(b"server: client 2 just left\n")
    ok2, got2 = c3.expect(b"server: client 2 just left\n")
    check(
        "client 2 disconnects: the others get 'server: client 2 just left'",
        ok1 and ok2,
        [("client 1 got", show(got1)), ("client 3 got", show(got2))],
    )

    c4 = Client(port)
    ok, got = c1.expect(b"server: client 4 just arrived\n")
    c3.read_for(0.1)
    check(
        "ids are never reused: the next client is 4",
        ok,
        [
            ("expected", show(b"server: client 4 just arrived\n")),
            ("got", show(got)),
        ],
    )

    _lazy_client(check, port, c1, c3, c4)

    if server.poll() is not None:
        ctx.fail("the server stopped", [("exit", str(server.returncode))])

    for c in (c1, c3, c4):
        c.close()
    time.sleep(0.5)
    after = _fd_count(server.pid)
    if baseline is not None and after is not None:
        check(
            "every client gone: the server's fds are back to where they"
            " started",
            after <= baseline,
            [
                ("open fds", f"{baseline} at the start, {after} now"),
                ("hint", "close() the socket of a client that leaves"),
            ],
        )
    else:
        check("fd count (skipped: no /proc)", True)

    check(
        "listens on 127.0.0.1 only",
        _listens_on_localhost(port),
        [(
            "hint",
            "servaddr.sin_addr.s_addr = htonl(2130706433); // 127.0.0.1",
        )],
    )


def _lazy_client(
    check: Checker, port: int, sender: Client, reader: Client, others: Client
) -> None:
    """A client that never reads must not slow down or block the others."""
    lazy = Client(port, rcvbuf=4096)
    for c in (sender, reader, others):
        c.read_for(0.1)
    line = b"x" * 200 + b"\n"
    count = 30000  # ~6 MB: more than the kernel buffers can hide
    expected_len = (len(b"client 1: ") + len(line)) * count + len(
        b"client 1: done\n"
    )
    got = {"reader": 0, "others": 0}
    done = threading.Event()

    def drain(client: Client, key: str) -> None:
        client.sock.settimeout(0.5)
        end = time.monotonic() + 25
        while time.monotonic() < end and not done.is_set():
            try:
                chunk = client.sock.recv(1 << 20)
            except socket.timeout:
                continue
            except OSError:
                return
            if not chunk:
                return
            got[key] += len(chunk)
            if got[key] >= expected_len:
                return

    threads = [
        threading.Thread(target=drain, args=(reader, "reader"), daemon=True),
        threading.Thread(target=drain, args=(others, "others"), daemon=True),
    ]
    for t in threads:
        t.start()
    start = time.monotonic()
    try:
        sender.sock.settimeout(25)
        sender.send(line * count + b"done\n")
        sent = True
    except OSError:
        sent = False
    for t in threads:
        t.join(timeout=max(0.1, 25 - (time.monotonic() - start)))
    done.set()
    took = time.monotonic() - start
    check(
        "a client that never reads is ignored, not waited for: the others get"
        " all 6 MB",
        sent
        and got["reader"] >= expected_len
        and got["others"] >= expected_len,
        [
            (
                "received",
                (
                    f"{got['reader']} and {got['others']} of {expected_len}"
                    f" bytes in {took:.1f}s"
                ),
            ),
            (
                "hint",
                (
                    "only send() to clients select() reports as writable;"
                    " never block on one client"
                ),
            ),
        ],
    )
    lazy.close()
    for c in (sender, reader, others):
        c.read_for(0.2)


def _listens_on_localhost(port: int) -> bool:
    try:
        lines = open("/proc/net/tcp").read().splitlines()[1:]
    except OSError:
        return True
    for line in lines:
        fields = line.split()
        local, state = fields[1], fields[3]
        addr, hex_port = local.split(":")
        if int(hex_port, 16) == port and state == "0A":
            return addr == "0100007F"
    return True
