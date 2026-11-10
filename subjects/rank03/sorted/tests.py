import io
import contextlib
import runpy


MODE = "script"  # run() receives the file path instead of a module


def run(path, check):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        runpy.run_path(path, run_name="__main__")
    expected = [
        "['fig', 'kiwi', 'banana']",
        "[('Ana', 8.5), ('Luis', 6.0)]",
        "[('Marta', 18), ('Ana', 20), ('Luis', 20)]",
    ]
    actual = output.getvalue().splitlines()
    check(
        "sorted",
        actual,
        expected,
    )
