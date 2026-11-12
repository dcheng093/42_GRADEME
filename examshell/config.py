"""Everything you might want to tweak lives here: name, levels, timers."""

from dataclasses import dataclass, replace
from pathlib import Path

APP_NAME = "GRADEME"
TAGLINE = "42 exam practice  ·  every rank  ·  C · C++ · Python"

# the top level only shows examshell/ and rendu/: subjects and scripts live in
# the package, your history in the hidden .examshell/
PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
SUBJECTS = PACKAGE / "subjects"
RENDU = ROOT / "rendu"
STATE_DIR = ROOT / ".examshell"
TRACE = STATE_DIR / "trace"

# seconds before a Python test run is killed (infinite loops)
TEST_TIMEOUT = 20
# C/C++: compiling + every case + valgrind; each run has its own limit too
NATIVE_TEST_TIMEOUT = 120

# banner reveals, confetti, count-ups. Off automatically when not a terminal.
ANIMATIONS = True

# Real-exam cooldown: wait before you may `test` again after the Nth failed
# attempt on the same level. Last value repeats. Set COOLDOWN_ENABLED = False
# to turn it off.
COOLDOWN_ENABLED = True
COOLDOWN_STEPS = (0, 30, 60, 120)


@dataclass(frozen=True)
class Level:
    theme: str
    pool: tuple[str, ...]
    # sub-folder under examshell/subjects/<rank>/, if the rank uses one
    folder: str = ""
    # practice only: never drawn in a real exam (rare subjects)
    extras: tuple[str, ...] = ()

    @property
    def practice_pool(self) -> tuple[str, ...]:
        return self.pool + self.extras


@dataclass(frozen=True)
class Rank:
    key: str
    title: str
    # display only: "c", "cpp", "python" or "mixed" (each question picks its
    # own harness)
    language: str
    time_limit: int  # seconds, real exam mode
    levels: tuple[Level, ...]
    exam: bool = True  # offered in real-exam mode (False = practice only)
    # "piscine", "current" = Python cursus, "old" = C cursus
    curriculum: str = "current"
    note: str = ""  # one line shown in the rank picker
    # points per level (grade capped at 100); 0 = 100 split evenly over the
    # levels
    points: int = 0
    # folders under examshell/subjects/ to find questions in (shared with
    # other ranks)
    borrow: tuple[str, ...] = ()
    # exam levels as indexes into `levels` (a pool can come back); () = each
    # once
    exam_plan: tuple[int, ...] = ()

    def exam_view(self) -> "Rank":
        """The rank as an exam plays it: `exam_plan` expanded into levels."""
        if not self.exam_plan:
            return self
        return replace(
            self,
            levels=tuple(self.levels[i] for i in self.exam_plan),
            exam_plan=(),
        )

    @property
    def level_points(self) -> int:
        return self.points or round(100 / len(self.levels))

    def grade(self, passed: int) -> int:
        """The grade out of 100 for `passed` levels."""
        if self.points:
            return min(100, passed * self.points)
        return round(passed * 100 / len(self.levels))

    @property
    def language_label(self) -> str:
        return LANGUAGE_LABELS.get(self.language, self.language)

    @property
    def cursus(self) -> str:
        """Short name of the rank's group: "Python" or "C"."""
        return next(
            (short for key, _, short in CURRICULA if key == self.curriculum),
            "",
        )

    @property
    def label(self) -> str:
        """The title, plus its cursus when another rank has the same title
        ("Rank 03  C")."""
        twins = sum(1 for r in RANKS.values() if r.title == self.title)
        return (
            f"{self.title}  {self.cursus}"
            if twins > 1 and self.cursus
            else self.title
        )


LANGUAGE_LABELS = {
    "c": "C",
    "cpp": "C++",
    "python": "Python",
    "mixed": "C / C++",
}
# (key, group header, short tag). Two ranks may share a title ("Rank 03"): the
# group tells them apart.
CURRICULA = (
    ("current", "Python cursus", "Python"),
    ("old", "C cursus", "C"),
    ("piscine", "Piscine", "Piscine"),
)


# ── Piscine: the weekly exams (pools as in wkratos/42-examshell) ──
# questions are shared with rank02; the ones only the piscine has are in
# examshell/subjects/piscine/
PISCINE_SOURCES = (
    "piscine",
    "rank02/level0",
    "rank02/level1",
    "rank02/level2",
    "rank02/level3",
)


def _piscine(
    pools: list[tuple[list[str], list[str]]],
    themes: list[str] | None = None,
) -> tuple[Level, ...]:
    """Levels from pools; `themes` names them (default: level by level)."""
    return tuple(
        Level(
            themes[i] if themes else f"step {i + 1}",
            pool=tuple(pool),
            extras=tuple(extra),
        )
        for i, (pool, extra) in enumerate(pools)
    )


# weeks 1 and 2 have 8 pools spread over 10 levels of 10 points (pool i*7//9)
_WEEK1 = [
    ["aff_a", "ft_countdown", "ft_print_numbers"],
    ["hello", "maff_alpha"],
    ["aff_first_param", "aff_last_param", "aff_z"],
    ["maff_revalpha", "only_a", "only_z"],
    ["ft_strcpy", "ft_strlen"],
    ["repeat_alpha", "search_and_replace", "ulstr"],
    ["first_word", "ft_putstr", "ft_swap"],
    ["rev_print", "rot_13", "rotone"],
]
_WEEK2 = [
    ["ft_strcpy", "ft_strlen", "repeat_alpha"],
    ["search_and_replace", "ulstr"],
    ["first_word", "ft_putstr", "ft_swap"],
    ["rev_print", "rot_13", "rotone"],
    ["ft_atoi", "ft_strdup", "inter"],
    ["last_word", "reverse_bits", "swap_bits", "union"],
    ["alpha_mirror", "do_op", "ft_strcmp", "ft_strrev"],
    ["is_power_of_2", "max", "print_bits", "wdmatch"],
]
_WEEK3 = [
    ["aff_a", "ft_countdown"],
    ["do_op", "first_word", "ft_print_numbers", "ft_strrev", "max", "wdmatch"],
    ["ft_strlen", "repeat_alpha"],
    [
        "expand_str",
        "ft_atoi_base",
        "ft_range",
        "lcm",
        "paramsum",
        "rev_print",
        "rot_13",
        "str_capitalizer",
        "tab_mult",
    ],
    ["rotone", "search_and_replace"],
    ["inter", "ulstr"],
    ["last_word", "union"],
    ["alpha_mirror", "wdmatch"],
    ["add_prime_sum", "epur_str"],
    ["expand_str", "paramsum"],
]
_FINAL = [
    ["aff_a", "ft_countdown"],
    ["first_word", "ft_print_numbers"],
    ["ft_strlen", "repeat_alpha"],
    ["rev_print", "rot_13"],
    ["rotone", "search_and_replace"],
    ["do_op", "ulstr"],
    ["inter", "last_word"],
    ["union", "wdmatch"],
    ["alpha_mirror", "print_bits"],
    ["reverse_bits", "swap_bits"],
    ["ft_putstr", "ft_strcpy"],
    ["ft_atoi", "ft_swap"],
    ["ft_strcmp", "ft_strdup"],
    ["ft_strrev", "is_power_of_2"],
    ["max", "only_a"],
    ["fprime", "rstr_capitalizer"],
    ["rostring", "tab_mult"],
]
# from older final exams: practice only
_FINAL_EXTRAS = {16: ["count_alpha", "str_maxlenoc"]}


def _spread(pools: list[list[str]], levels: int = 10) -> tuple[int, ...]:
    """Exam levels over fewer pools, the way the piscine exams do it
    (pool i*7//9 for 8)."""
    return tuple(i * (len(pools) - 1) // (levels - 1) for i in range(levels))


PISCINE = {
    "piscine_exam00": Rank(
        key="piscine_exam00",
        title="Exam 00",
        language="c",
        time_limit=4 * 60 * 60,
        curriculum="piscine",
        note="week 1",
        points=10,
        borrow=PISCINE_SOURCES,
        levels=_piscine([(p, []) for p in _WEEK1]),
        exam_plan=_spread(_WEEK1),
    ),
    "piscine_exam01": Rank(
        key="piscine_exam01",
        title="Exam 01",
        language="c",
        time_limit=4 * 60 * 60,
        curriculum="piscine",
        note="week 2",
        points=10,
        borrow=PISCINE_SOURCES,
        levels=_piscine([(p, []) for p in _WEEK2]),
        exam_plan=_spread(_WEEK2),
    ),
    "piscine_exam02": Rank(
        key="piscine_exam02",
        title="Exam 02",
        language="c",
        time_limit=4 * 60 * 60,
        curriculum="piscine",
        note="week 3",
        points=10,
        borrow=PISCINE_SOURCES,
        levels=_piscine([(p, []) for p in _WEEK3]),
    ),
    "piscine_final": Rank(
        key="piscine_final",
        title="Final exam",
        language="c",
        time_limit=8 * 60 * 60,
        curriculum="piscine",
        note="week 4",
        points=6,
        borrow=PISCINE_SOURCES,
        levels=_piscine(
            [(p, _FINAL_EXTRAS.get(i, [])) for i, p in enumerate(_FINAL)]
        ),
    ),
}

RANKS: dict[str, Rank] = {
    **PISCINE,
    "rank02": Rank(
        key="rank02",
        title="Rank 02",
        language="c",
        time_limit=3 * 60 * 60,
        levels=(
            Level(
                "foundations",
                folder="level0",
                pool=(
                    "first_word",
                    "fizzbuzz",
                    "ft_putstr",
                    "ft_strcpy",
                    "ft_strlen",
                    "ft_swap",
                    "repeat_alpha",
                    "rev_print",
                    "rot_13",
                    "rotone",
                    "search_and_replace",
                    "ulstr",
                ),
            ),
            Level(
                "intermediate",
                folder="level1",
                pool=(
                    "alpha_mirror",
                    "camel_to_snake",
                    "do_op",
                    "ft_atoi",
                    "ft_strcmp",
                    "ft_strcspn",
                    "ft_strdup",
                    "ft_strrev",
                    "inter",
                    "is_power_of_2",
                    "last_word",
                    "max",
                    "print_bits",
                    "reverse_bits",
                    "snake_to_camel",
                    "swap_bits",
                    "union",
                    "wdmatch",
                ),
                extras=("ft_strpbrk", "ft_strspn"),
            ),  # on 42exam.net, rarely seen in exams
            Level(
                "advanced",
                folder="level2",
                pool=(
                    "add_prime_sum",
                    "epur_str",
                    "expand_str",
                    "ft_atoi_base",
                    "ft_list_size",
                    "ft_range",
                    "ft_rrange",
                    "hidenp",
                    "lcm",
                    "paramsum",
                    "pgcd",
                    "print_hex",
                    "rstr_capitalizer",
                    "str_capitalizer",
                    "tab_mult",
                ),
            ),
            Level(
                "expert",
                folder="level3",
                pool=(
                    "flood_fill",
                    "fprime",
                    "ft_itoa",
                    "ft_list_foreach",
                    "ft_list_remove_if",
                    "ft_split",
                    "rev_wstr",
                    "rostring",
                    "sort_int_tab",
                    "sort_list",
                ),
            ),
        ),
    ),
    # Python ranks 03-06: pools from 42exam.net (examshell/scripts/data/),
    # built by examshell/scripts/import_python.py
    "rank03": Rank(
        key="rank03",
        title="Rank 03",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level("easy", pool=("py_bracket_validator", "py_cryptic_sorter")),
            Level("easy", pool=("py_echo_validator", "py_mirror_matrix")),
            Level(
                "medium",
                pool=(
                    "py_hidenp",
                    "py_inter",
                    "py_number_base_converter",
                    "py_pattern_tracker",
                ),
            ),
            Level(
                "medium",
                pool=(
                    "py_anagram",
                    "py_shadow_merge",
                    "py_string_permutation_checker",
                ),
            ),
            Level("hard", pool=("py_string_sculptor", "py_twist_sequence")),
            Level("hard", pool=("py_whisper_cipher",)),
        ),
    ),
    "rank04": Rank(
        key="rank04",
        title="Rank 04",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level(
                "arrays",
                pool=("py_array_rotation_detector", "py_constellation_mapper"),
            ),
            Level(
                "sorted lists",
                pool=("py_list_intersection_finder", "py_merge_sorted_lists"),
            ),
            Level(
                "dp & graphs",
                pool=(
                    "py_palindrome_partitioner",
                    "py_package_dependency_resolver",
                ),
            ),
            Level("sliding window", pool=("py_sliding_window_maximum",)),
        ),
    ),
    "rank05": Rank(
        key="rank05",
        title="Rank 05",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level(
                "strings & matrices",
                pool=(
                    "py_compress_decompress",
                    "py_spiral_matrix",
                    "py_room_scheduler",
                ),
            ),
            Level(
                "graphs & grids",
                pool=("py_graph_cycle_detector", "py_island_matrix_counter"),
            ),
            Level("search", pool=("py_prism_detector", "py_word_ladder")),
        ),
    ),
    "rank06": Rank(
        key="rank06",
        title="Rank 06",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level(
                "data structures",
                pool=(
                    "prefix_dictionary",
                    "pack_strings",
                    "task_order",
                    "redundant_link",
                    "trie_autocomplete",
                ),
            ),
            Level(
                "advanced structures",
                pool=(
                    "union_find_system",
                    "cache_keeper",
                    "min_heap",
                    "bridge_finder",
                ),
            ),
        ),
    ),
    # ── C cursus (the exams before the switch to Python) ──
    "old_rank03": Rank(
        key="old_rank03",
        title="Rank 03",
        language="c",
        time_limit=3 * 60 * 60,
        curriculum="old",
        note="gnl, filter, scanf, then backtracking",
        levels=(
            Level("io", pool=("broken_gnl", "filter", "scanf")),
            Level(
                "backtracking",
                pool=("n_queens", "permutations", "powerset", "rip", "tsp"),
            ),
        ),
    ),
    "old_rank04": Rank(
        key="old_rank04",
        title="Rank 04",
        language="c",
        time_limit=3 * 60 * 60,
        curriculum="old",
        note="processes and pipes, then parsers",
        levels=(
            Level("processes", pool=("ft_popen", "picoshell", "sandbox")),
            Level("parsers", pool=("argo", "vbc")),
        ),
    ),
    "old_rank05": Rank(
        key="old_rank05",
        title="Rank 05",
        language="mixed",
        time_limit=3 * 60 * 60,
        curriculum="old",
        note="C++98 classes, then bsq / life in C",
        levels=(
            Level("C++ classes", pool=("bigint", "polyset", "vect2")),
            Level("C programs", pool=("bsq", "life")),
        ),
    ),
    "old_rank06": Rank(
        key="old_rank06",
        title="Rank 06",
        language="mixed",
        time_limit=3 * 60 * 60,
        curriculum="old",
        note="a chat server in C, or a key-value server in C++",
        levels=(Level("servers", pool=("mini_serv", "mini_db")),),
    ),
    # The Python pool before the 42exam.net one (2025 beta): practice only
    "rank03_legacy": Rank(
        key="rank03_legacy",
        title="Rank 03 · Python beta pool",
        language="python",
        time_limit=3 * 60 * 60,
        exam=False,
        note="the first Python pool, before the current one",
        levels=(
            Level(
                "strings",
                pool=("alternate_case", "capitalize_words", "valid_anagram"),
            ),
            Level(
                "parsing", pool=("atoi", "py_echo_validator", "whisper_lipher")
            ),
            Level(
                "sorting",
                pool=("sorted", "merge_and_sort_desc", "customSortString"),
            ),
            Level(
                "counting & hashing",
                pool=("twoSum", "topKFrequent", "py_pattern_tracker"),
            ),
            Level(
                "matrices",
                pool=("mirror_matrix", "mirror_matrix_vertical", "rotate_90"),
            ),
            Level("algorithms", pool=("brackets", "convert_base")),
        ),
    ),
}

LANGUAGES = ("en", "de", "fr", "es", "it", "ru", "tr", "zh", "ar")
# Login shown on the examshell screens. By default it is your computer's
# account name ($USER). To use a different one without committing it, put it
# in .examshell/login (gitignored) or set GRADEME_LOGIN.
EXAM_LOGIN_FILE = STATE_DIR / "login"
