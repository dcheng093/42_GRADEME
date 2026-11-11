"""Everything you might want to tweak lives here: name, levels, timers."""

from dataclasses import dataclass
from pathlib import Path

APP_NAME = "GRADEME"
TAGLINE = "42 exam practice  ·  every rank  ·  C · C++ · Python"

ROOT = Path(__file__).resolve().parent.parent
SUBJECTS = ROOT / "subjects"
RENDU = ROOT / "rendu"
TRACE = ROOT / "trace"
STATE_DIR = ROOT / ".examshell"

TEST_TIMEOUT = 20  # seconds before a Python test run is killed (infinite loops)
NATIVE_TEST_TIMEOUT = 120  # C/C++: compiling + every case + valgrind; each run has its own limit too

ANIMATIONS = True  # banner reveals, confetti, count-ups. Off automatically when not a terminal.

# Real-exam cooldown: wait before you may `test` again after the Nth failed
# attempt on the same level. Last value repeats. Set COOLDOWN_ENABLED = False
# to turn it off.
COOLDOWN_ENABLED = True
COOLDOWN_STEPS = (0, 30, 60, 120)


@dataclass(frozen=True)
class Level:
    theme: str
    pool: tuple
    folder: str = ""  # sub-folder under subjects/<rank>/, if the rank uses one
    extras: tuple = ()  # practice only: never drawn in a real exam (rare subjects)

    @property
    def practice_pool(self):
        return self.pool + self.extras


@dataclass(frozen=True)
class Rank:
    key: str
    title: str
    language: str  # display only: "c", "cpp", "python" or "mixed" (each question picks its own harness)
    time_limit: int  # seconds, real exam mode
    levels: tuple
    exam: bool = True  # offered in real-exam mode (False = practice only)
    curriculum: str = "current"  # "current" (2025+: rank02 C, ranks 03-06 Python) or "old"
    note: str = ""  # one line shown in the rank picker

    @property
    def language_label(self):
        return LANGUAGE_LABELS.get(self.language, self.language)


LANGUAGE_LABELS = {"c": "C", "cpp": "C++", "python": "Python", "mixed": "C / C++"}
CURRICULA = (("current", "current curriculum"), ("old", "old curriculum"))


RANKS = {
    "rank02": Rank(
        key="rank02",
        title="Rank 02",
        language="c",
        time_limit=3 * 60 * 60,
        levels=(
            Level("foundations", folder="level0", pool=(
                "first_word", "fizzbuzz", "ft_putstr", "ft_strcpy", "ft_strlen",
                "ft_swap", "repeat_alpha", "rev_print", "rot_13", "rotone",
                "search_and_replace", "ulstr",
            )),
            Level("intermediate", folder="level1", pool=(
                "alpha_mirror", "camel_to_snake", "do_op", "ft_atoi", "ft_strcmp",
                "ft_strcspn", "ft_strdup", "ft_strrev", "inter", "is_power_of_2",
                "last_word", "max", "print_bits", "reverse_bits", "snake_to_camel",
                "swap_bits", "union", "wdmatch",
            ), extras=("ft_strpbrk", "ft_strspn")),  # on 42exam.net, rarely seen in exams
            Level("advanced", folder="level2", pool=(
                "add_prime_sum", "epur_str", "expand_str", "ft_atoi_base",
                "ft_list_size", "ft_range", "ft_rrange", "hidenp", "lcm",
                "paramsum", "pgcd", "print_hex", "rstr_capitalizer",
                "str_capitalizer", "tab_mult",
            )),
            Level("expert", folder="level3", pool=(
                "flood_fill", "fprime", "ft_itoa", "ft_list_foreach",
                "ft_list_remove_if", "ft_split", "rev_wstr", "rostring",
                "sort_int_tab", "sort_list",
            )),
        ),
    ),
    # Python ranks 03-06: pools from 42exam.net (scripts/data/), built by scripts/import_python.py
    "rank03": Rank(
        key="rank03",
        title="Rank 03",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level("easy", pool=("py_bracket_validator", "py_cryptic_sorter")),
            Level("easy", pool=("py_echo_validator", "py_mirror_matrix")),
            Level("medium", pool=("py_hidenp", "py_inter", "py_number_base_converter", "py_pattern_tracker")),
            Level("medium", pool=("py_anagram", "py_shadow_merge", "py_string_permutation_checker")),
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
            Level("arrays", pool=("py_array_rotation_detector", "py_constellation_mapper")),
            Level("sorted lists", pool=("py_list_intersection_finder", "py_merge_sorted_lists")),
            Level("dp & graphs", pool=("py_palindrome_partitioner", "py_package_dependency_resolver")),
            Level("sliding window", pool=("py_sliding_window_maximum",)),
        ),
    ),
    "rank05": Rank(
        key="rank05",
        title="Rank 05",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level("strings & matrices", pool=("py_compress_decompress", "py_spiral_matrix", "py_room_scheduler")),
            Level("graphs & grids", pool=("py_graph_cycle_detector", "py_island_matrix_counter")),
            Level("search", pool=("py_prism_detector", "py_word_ladder")),
        ),
    ),
    "rank06": Rank(
        key="rank06",
        title="Rank 06",
        language="python",
        time_limit=3 * 60 * 60,
        levels=(
            Level("data structures", pool=("prefix_dictionary", "pack_strings", "task_order",
                                           "redundant_link", "trie_autocomplete")),
            Level("advanced structures", pool=("union_find_system", "cache_keeper", "min_heap", "bridge_finder")),
        ),
    ),
    # ── old curriculum (before the Python ranks) ──
    "old_rank03": Rank(
        key="old_rank03",
        title="Rank 03 · old",
        language="c",
        time_limit=3 * 60 * 60,
        curriculum="old",
        note="gnl, filter, scanf, then backtracking",
        levels=(
            Level("io", pool=("broken_gnl", "filter", "scanf")),
            Level("backtracking", pool=("n_queens", "permutations", "powerset", "rip", "tsp")),
        ),
    ),
    "old_rank05": Rank(
        key="old_rank05",
        title="Rank 05 · old",
        language="mixed",
        time_limit=3 * 60 * 60,
        curriculum="old",
        note="C++98 classes, then bsq / life in C",
        levels=(
            Level("C++ classes", pool=("bigint", "polyset", "vect2")),
            Level("C programs", pool=("bsq", "life")),
        ),
    ),
    # The Python pool before the 42exam.net one (2025 beta): practice only
    "rank03_legacy": Rank(
        key="rank03_legacy",
        title="Rank 03 · Python beta pool",
        language="python",
        time_limit=3 * 60 * 60,
        exam=False,
        curriculum="old",
        note="the first Python pool, before the current one",
        levels=(
            Level("strings", pool=("alternate_case", "capitalize_words", "valid_anagram")),
            Level("parsing", pool=("atoi", "py_echo_validator", "whisper_lipher")),
            Level("sorting", pool=("sorted", "merge_and_sort_desc", "customSortString")),
            Level("counting & hashing", pool=("twoSum", "topKFrequent", "py_pattern_tracker")),
            Level("matrices", pool=("mirror_matrix", "mirror_matrix_vertical", "rotate_90")),
            Level("algorithms", pool=("brackets", "convert_base")),
        ),
    ),
}

LANGUAGES = ("en", "de", "fr", "es", "it", "ru", "tr", "zh", "ar")
# Login shown on the examshell screens. By default it is your computer's account
# name ($USER). To use a different one without committing it, put it in
# .examshell/login (gitignored) or set GRADEME_LOGIN.
EXAM_LOGIN_FILE = STATE_DIR / "login"
