"""Everything you might want to tweak lives here: name, levels, timers."""

from dataclasses import dataclass
from pathlib import Path

APP_NAME = "GRADEME"
TAGLINE = "42 exam practice  ·  rank02 in C  ·  rank03 in Python"

ROOT = Path(__file__).resolve().parent.parent
SUBJECTS = ROOT / "subjects"
RENDU = ROOT / "rendu"
TRACE = ROOT / "trace"
STATE_DIR = ROOT / ".examshell"

TEST_TIMEOUT = 10  # seconds before a test run is killed (infinite loops)

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


@dataclass(frozen=True)
class Rank:
    key: str
    title: str
    language: str  # "c" or "python"
    time_limit: int  # seconds, real exam mode
    levels: tuple


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
            )),
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
    "rank03": Rank(
        key="rank03",
        title="Rank 03",
        language="python",
        time_limit=3 * 60 * 60,
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
