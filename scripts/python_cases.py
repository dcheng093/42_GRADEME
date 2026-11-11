"""Extra test cases for the Python ranks, used by scripts/import_python.py.

For each subject: EDGE cases (hand-picked), RANDOM cases (seeded, so the
generated tests are stable), and where the subject is ambiguous, ALTERNATES:
other readings of the subject. A random case is only kept when every reading
gives the same answer, so a reasonable solution never fails on a detail the
subject doesn't specify.

Arguments are tuples. Expected values are computed with the reference
solution (subjects/<rank>/<name>/solution.py), never written here.
"""

import random
import string

# ── extra cases, as argument tuples ─────────────────────────────────────────
def _word(rng, alphabet, lo=0, hi=12):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(lo, hi)))


def _random_rank03(name, rng):
    letters, digits = string.ascii_letters, string.digits
    if name == "py_bracket_validator":
        out = []
        for _ in range(40):
            out.append((_word(rng, "()[]{}ab ", 0, 14),))
        for _ in range(10):  # guaranteed-valid nests
            s = ""
            for _ in range(rng.randint(1, 6)):
                o, c = rng.choice(["()", "[]", "{}"])
                s = rng.choice([o + s + c, s + o + c, o + c + s])
            out.append((s,))
        return out
    if name == "py_cryptic_sorter":
        return [([_word(rng, "abcAEoUz", 0, 5) for _ in range(rng.randint(0, 9))],) for _ in range(30)]
    if name == "py_echo_validator":
        out = []
        for _ in range(20):
            half = _word(rng, "abcAB", 1, 6)
            mid = rng.choice(["", "x", "Z"])
            s = half + mid + half[::-1]
            s = "".join(c.upper() if rng.random() < 0.3 else c for c in s)
            s = "".join(c + (rng.choice(" ,.!1") if rng.random() < 0.2 else "") for c in s)
            out.append((s,))
        out += [(_word(rng, "abc ", 1, 8),) for _ in range(15)]
        return out
    if name == "py_mirror_matrix":
        out = []
        for _ in range(20):
            w = rng.randint(1, 6)
            out.append(([[rng.randint(-50, 50) for _ in range(w)] for _ in range(rng.randint(1, 5))],))
        return out
    if name == "py_hidenp":
        return [(_word(rng, "abc", 0, 4), _word(rng, "abcd1", 0, 10)) for _ in range(40)]
    if name == "py_inter":
        return [(_word(rng, "abcdeAB1 ", 0, 10), _word(rng, "abcxyzA ", 0, 10)) for _ in range(40)]
    if name == "py_number_base_converter":
        out = []
        for _ in range(40):
            n, fb, tb = rng.randint(0, 10 ** 9), rng.randint(2, 36), rng.randint(2, 36)
            s = ""
            while True:
                n, r = divmod(n, fb)
                s = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[r] + s
                if not n:
                    break
            out.append((s, fb, tb))
        return out
    if name == "py_pattern_tracker":
        return [(_word(rng, digits + "ab", 0, 16),) for _ in range(40)]
    if name == "py_anagram":
        out = []
        for _ in range(20):
            a = _word(rng, "abcdeABC ", 1, 10)
            b = list(a.replace(" ", ""))
            rng.shuffle(b)
            b = "".join(c.swapcase() if rng.random() < 0.3 else c for c in b)
            if rng.random() < 0.4:
                b += rng.choice("ab")
            out.append((a, b))
        return out
    if name == "py_shadow_merge":
        return [(sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 8))),
                 sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 8)))) for _ in range(30)]
    if name == "py_string_permutation_checker":
        out = []
        for _ in range(20):
            a = _word(rng, "abcAB ,!", 0, 10)
            b = list(a)
            rng.shuffle(b)
            b = "".join(b)
            if rng.random() < 0.4 and b:
                b = b[:-1] + rng.choice("aAz ")
            out.append((a, b))
        return out
    if name == "py_string_sculptor":
        return [(_word(rng, letters + digits + " .!,", 0, 20),) for _ in range(30)]
    if name == "py_twist_sequence":
        return [([rng.randint(-9, 9) for _ in range(rng.randint(0, 8))], rng.randint(0, 20)) for _ in range(30)]
    if name == "py_whisper_cipher":
        return [(_word(rng, letters + digits + " !.", 0, 20), rng.randint(-60, 60)) for _ in range(30)]
    return []


EDGE = {
    "py_bracket_validator": [("a",), ("(",), (")",), ("{[()()]}",), ("((((((((((",), ("([]{}){}[()]",),
                             ("}{",), ("[(])",), ("text with (brackets [and {nesting}])",), ("([)",)],
    "py_cryptic_sorter": [(["b", "a"],), (["B", "a"],), (["a", "A", "a"],), (["zz", "a", "Bb", "aa"],),
                          (["abc", "ABC", "aBc"],), (["one", "two", "six", "ten"],), (["", "a", ""],),
                          (["Zebra", "apple", "Mango", "kiwi", "fig"],)],
    "py_echo_validator": [("a",), ("Aa",), ("ab",), ("No lemon, no melon",), ("Step on no pets",),
                          ("12321",), ("a1b2a",), ("Never odd or even",), ("abca",), ("!!!",)],
    "py_mirror_matrix": [([],), ([[]],), ([[1], [2], [3]],), ([[0, 0], [0, 0]],), ([[1, 2, 3], [4, 5, 6], [7, 8, 9]],)],
    "py_hidenp": [("", ""), ("a", ""), ("a", "a"), ("A", "a"), ("abc", "abc"), ("abc", "cba"),
                  ("aab", "ab"), ("ab", "aab"), ("xyz", "x y z")],
    "py_inter": [("", ""), ("abc", ""), ("aaa", "a"), ("abc", "cba"), ("Aa", "a"), ("a b", " "),
                 ("padinton", "paqefwtdjetyiytjneytjoeyjnejeyj")],
    "py_number_base_converter": [("0", 10, 2), ("0", 2, 36), ("1", 2, 2), ("10", 10, 10), ("ZZ", 36, 10),
                                 ("1295", 10, 36), ("777", 8, 2), ("11111111", 2, 16), ("0010", 2, 10),
                                 ("2", 2, 10), ("1", 10, 37), ("1", 37, 10), ("1", 0, 10), ("", 10, 2),
                                 ("12a", 10, 2), ("1.5", 10, 2), ("4294967295", 10, 16)],
    "py_pattern_tracker": [("",), ("1",), ("12",), ("21",), ("90",), ("89",), ("0123456789",),
                           ("1 2",), ("1212",), ("a1b23c45",)],
    "py_anagram": [("a", "A"), ("a", "b"), (" ", ""), ("abc", "ab"), ("aab", "abb"),
                   ("Astronomer", "Moon starer"), ("The eyes", "They see"), ("abc", "cba ")],
    "py_shadow_merge": [([], []), ([1], []), ([5], [1]), ([-3, 0], [-5, -1, 7]), ([2, 2, 2], [2, 2]),
                        ([1, 2, 3], [1, 2, 3]), ([10, 20, 30], [1, 2, 3])],
    "py_string_permutation_checker": [("a", "a"), ("a", "A"), (" ", ""), ("ab", "ba "), ("aab", "abb"),
                                      ("a!b", "b!a"), ("dormitory", "dirty room")],
    "py_string_sculptor": [("a",), ("A",), ("   ",), ("123",), ("a b c",), ("ab  cd",),
                           ("HELLO WORLD",), ("x1y2z3",), ("Hi! How are you?",)],
    "py_twist_sequence": [([1], 0), ([1], 100), ([1, 2], 1), ([1, 2], 2), ([1, 2, 3, 4, 5], 5),
                          ([1, 2, 3, 4, 5], 7), ([0, 0, 1], 1), ([], 0)],
    "py_whisper_cipher": [("a", 1), ("z", 1), ("Z", 1), ("a", 26), ("a", 52), ("abc", 0), ("abc", -26),
                          ("Hello, World!", 13), ("Uryyb, Jbeyq!", -13), ("1234 !?", 7), ("aZ", -1)],
}
NO_MUTATION = {"py_mirror_matrix"}  # subject says "return a new matrix"



# ── rank 04 · 05 · 06 ───────────────────────────────────────────────────────
EDGE.update({
    # rank 04
    "py_array_rotation_detector": [([1], [1]), ([1], [2]), ([1, 1, 2], [1, 2, 1]), ([1, 1, 2], [1, 2, 2]),
                                   ([1, 2, 3], [1, 2, 3]), ([1, 2, 1, 2], [2, 1, 2, 1]), ([], [1]),
                                   (["a", "b"], ["b", "a"]), ([0, 0, 0], [0, 0, 0])],
    "py_constellation_mapper": [([], 0), ([(0, 0)], 1), ([(-1, 0), (0, -1)], 2), ([(3, 0)], 3),
                                ([(0, 3)], 3), ([(2, 2), (0, 0)], 3), ([(1, 1)], 4)],
    "py_list_intersection_finder": [([[]],), ([[], []],), ([[1, 1, 1]],), ([[1, 2], [1, 2], [1, 2]],),
                                    ([[-3, -1, 0], [-3, 0, 5]],), ([[1, 2, 3], [3], [3, 4]],)],
    "py_merge_sorted_lists": [([],), ([[], []],), ([[1]],), ([[1, 2, 3]],), ([[3], [2], [1]],),
                              ([[-2, -2], [-2], [-3, 5]],), ([[1, 4], [], [2, 3], []],)],
    "py_palindrome_partitioner": [("",), ("a",), ("aa",), ("ab",), ("racecar",), ("abba",), ("abcba",),
                                  ("aabb",), ("abacdc",), ("banana",), ("noonabbad",), ("abcdefg",)],
    "py_package_dependency_resolver": [
        ({"a": []},), ({"a": ["a"]},), ({"a": ["missing"]},), ({"b": [], "a": []},),
        ({"a": ["b"], "b": ["c"], "c": ["a"]},), ({"a": [], "b": ["a"], "c": ["c"]},),
        ({"lib": ["core"], "core": [], "app": ["lib", "ui"], "ui": ["core"]},),
        ({"z": [], "y": ["z"], "x": ["missing", "y"]},)],
    "py_sliding_window_maximum": [([1], 1), ([1], 2), ([4, 4, 4], 2), ([-1, -5, -3], 2), ([2, 1], -1),
                                  ([9, 8, 7, 6], 4), ([1, 3, 1, 3, 1], 2), ([7, 2, 4], 1)],
    # rank 05
    "py_compress_decompress": [("compress", ("a",)), ("compress", ("aaaaaaaaaaaa",)), ("compress", ("abc",)),
                               ("compress", ("aabbaa",)), ("compress", ("  !!",)), ("decompress", ("",)),
                               ("decompress", ("a12",)), ("decompress", ("abc",)), ("decompress", ("x1y2z3",)),
                               ("decompress", ("a10b",))],
    "py_spiral_matrix": [(0,), (2,), (4,), (5,)],
    "py_graph_cycle_detector": [({0: [0]},), ({0: []},), ({0: [1]},), ({0: [1, 2], 1: [2], 2: []},),
                                ({0: [1], 1: [0]},), ({0: [], 1: [2], 2: [3], 3: [1]},),
                                ({5: [6], 6: [7], 7: [], 8: [8]},)],
    "py_room_scheduler": [([[1, 5]],), ([[1, 5], [2, 6], [3, 7]],), ([[7, 9], [1, 3], [4, 6]],),
                          ([[0, 10], [11, 20], [21, 30]],), ([[5, 8], [1, 4], [2, 9], [6, 7]],)],
    "py_island_matrix_counter": [([[]],), ([["0"]],), ([["1"]],), ([["1", "0", "1"]],),
                                 ([["1"], ["0"], ["1"]],), ([["1", "0"], ["0", "1"]],),
                                 ([["1", "1"], ["1", "1"]],), ([["1", "0", "1"], ["1", "1", "1"]],)],
    "py_prism_detector": [(["CAT"], ""), (["ABC", "DEF"], "XY"), (["ABA"], "AB"), (["AB", "BA"], "AB"),
                          (["TAC"], "CAT"), (["C", "A", "T"], "CAT"), (["T", "A", "C"], "CAT"),
                          (["C..", ".A.", "..T"], "CAT"), (["T..", ".A.", "..C"], "CAT"),
                          (["ABAB"], "ABA")],
    "py_word_ladder": [("a", "c", ["a", "b", "c"]), ("hot", "dog", ["hot", "dog"]), ("hot", "dog", ["hot", "dot", "dog"]),
                       ("lost", "cost", ["most", "fist", "lost", "cost", "fish"]),
                       ("hit", "cog", []), ("abc", "xyz", ["xyz"])],
    # rank 06 (function subjects)
    "redundant_link": [([[1, 2], [2, 1]],), ([[1, 2], [2, 3], [3, 1]],), ([[2, 3], [1, 2], [3, 1]],),
                       ([[1, 2], [2, 3], [3, 4], [4, 5], [5, 1]],), ([[3, 4], [1, 2], [2, 4], [3, 5], [2, 5]],)],
    "task_order": [(1, []), (0, []), (1, [[0, 0]]), (3, [[0, 1], [0, 2]]), (3, [[2, 0], [1, 0]]),
                   (5, [[4, 3], [3, 2], [2, 1], [1, 0]]), (4, [[1, 0], [2, 1], [0, 2]]), (4, [[3, 0], [3, 1]])],
    "trie_autocomplete": [(["a", "a", "a"], "a"), (["Apple", "apple"], "a"), (["Apple", "apple"], "A"),
                          (["b", "a", "c"], ""), (["abc"], "abcd"), (["car", "cart", "carbon"], "cart")],
    "bridge_finder": [({0: []},), ({1: [2], 2: [1, 3], 3: [2, 4], 4: [3]},),
                      ({0: [1, 2], 1: [0, 2], 2: [0, 1, 3], 3: [2, 4, 5], 4: [3, 5], 5: [3, 4]},),
                      ({0: [1], 1: [0], 2: [3], 3: [2]},), ({10: [3], 3: [10]},)],
    "pack_strings": [([],), ([""],), (["", ""],), (["#"],), (["3#abc"],), (["a:b", "c#d", ""],),
                     (["line\nbreak", "tab\there"],), (["0", "00", "10#"],), (["日本", "émoji ✓"],),
                     (["x" * 120],)],
})
NO_MUTATION.update({"py_merge_sorted_lists", "py_list_intersection_finder", "py_array_rotation_detector",
                    "py_island_matrix_counter"})
UNORDERED = {"py_prism_detector"}  # the subject gives no order for the matches

# class subjects: the variable name the examples use, and op generators below
CLASSES = {
    "prefix_dictionary": ("PrefixDictionary", "d"),
    "union_find_system": ("UnionFind", "uf"),
    "cache_keeper": ("CacheKeeper", "c"),
    "min_heap": ("MinHeap", "h"),
}
ROUNDTRIP = {"pack_strings": ("pack", "unpack")}
# signatures the published data leaves incomplete
SIGNATURES = {
    "py_compress_decompress": "def compress(s: str) -> str:\ndef decompress(s: str) -> str:",
}


# ── random cases ────────────────────────────────────────────────────────────
def _sorted_ints(rng, lo, hi, n_lo, n_hi):
    return sorted(rng.randint(lo, hi) for _ in range(rng.randint(n_lo, n_hi)))


def _rotate(values, k):
    return values[k:] + values[:k] if values else values


def _tree_edges(rng, n):
    """A random tree on 1..n plus one extra edge, shuffled."""
    nodes = list(range(1, n + 1))
    rng.shuffle(nodes)
    edges = [[nodes[i], nodes[rng.randrange(i)]] for i in range(1, n)]
    while True:
        u, v = rng.sample(range(1, n + 1), 2)
        if [u, v] not in edges and [v, u] not in edges:
            break
    edges.append([u, v])
    rng.shuffle(edges)
    return [e if rng.random() < 0.5 else e[::-1] for e in edges]


def _undirected(rng, n, p):
    graph = {i: [] for i in range(n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                graph[u].append(v)
                graph[v].append(u)
    return graph


def _random_new(name, rng):
    out = []
    if name == "py_array_rotation_detector":
        for _ in range(30):
            a = [rng.randint(0, 3) for _ in range(rng.randint(0, 7))]
            b = _rotate(a, rng.randint(0, len(a))) if a else []
            if rng.random() < 0.4 and b:
                b = b[:]
                b[rng.randrange(len(b))] = rng.randint(0, 3)
            if rng.random() < 0.15:
                b = b[::-1]
            out.append((a, b))
    elif name == "py_constellation_mapper":
        for _ in range(25):
            dim = rng.randint(1, 6)
            stars = [(rng.randint(-1, dim), rng.randint(-1, dim)) for _ in range(rng.randint(0, 8))]
            out.append((stars, dim))
    elif name == "py_list_intersection_finder":
        for _ in range(30):
            out.append(([_sorted_ints(rng, 0, 8, 0, 7) for _ in range(rng.randint(1, 4))],))
    elif name == "py_merge_sorted_lists":
        for _ in range(30):
            out.append(([_sorted_ints(rng, -20, 20, 0, 6) for _ in range(rng.randint(0, 5))],))
    elif name == "py_palindrome_partitioner":
        out = [("".join(rng.choice("ab" if i % 2 else "abc") for _ in range(rng.randint(2, 14))),)
               for i in range(30)]
    elif name == "py_package_dependency_resolver":
        for _ in range(40):
            names = rng.sample(["app", "api", "cli", "core", "db", "log", "net", "ui", "web", "zip"], rng.randint(1, 7))
            order = names[:]
            rng.shuffle(order)
            pkgs = {}
            for i, n in enumerate(order):
                deps = rng.sample(order[:i], rng.randint(0, min(i, 2))) if i else []
                if rng.random() < 0.15:
                    deps.append("missing")
                pkgs[n] = deps
            if rng.random() < 0.2 and len(order) > 1:  # close a cycle
                pkgs[order[0]].append(order[-1])
            out.append((dict(sorted(pkgs.items(), key=lambda kv: rng.random())),))
    elif name == "py_sliding_window_maximum":
        for _ in range(30):
            nums = [rng.randint(-9, 9) for _ in range(rng.randint(0, 10))]
            out.append((nums, rng.randint(0, len(nums) + 1)))
    elif name == "py_compress_decompress":
        from_rng = []
        for _ in range(20):
            s = "".join(rng.choice("aab c") * rng.choice([1, 1, 2, 3, 11]) for _ in range(rng.randint(0, 6)))
            from_rng.append(("compress", (s,)))
        for _ in range(15):
            s = "".join(rng.choice("xyz ") + rng.choice(["", "", "2", "9", "12"]) for _ in range(rng.randint(0, 5)))
            from_rng.append(("decompress", (s,)))
        return from_rng
    elif name == "py_spiral_matrix":
        out = [(n,) for n in (6, 7, 8)]
    elif name == "py_graph_cycle_detector":
        for _ in range(30):
            n = rng.randint(1, 7)
            graph = {}
            for u in range(n):
                graph[u] = [v for v in range(n) if v != u and rng.random() < 0.25]
            if rng.random() < 0.6:  # make it a DAG
                graph = {u: [v for v in vs if v > u] for u, vs in graph.items()}
            out.append((graph,))
    elif name == "py_room_scheduler":
        for _ in range(30):
            starts = rng.sample(range(0, 40), rng.randint(0, 7))
            out.append(([[s, s + rng.randint(1, 15)] for s in starts],))
    elif name == "py_island_matrix_counter":
        for _ in range(25):
            h, w = rng.randint(1, 6), rng.randint(1, 6)
            out.append(([[rng.choice("0011") for _ in range(w)] for _ in range(h)],))
    elif name == "py_prism_detector":
        for _ in range(40):
            h, w = rng.randint(1, 5), rng.randint(1, 5)
            grid = ["".join(rng.choice("CAT") for _ in range(w)) for _ in range(h)]
            pattern = "".join(rng.choice("CAT") for _ in range(rng.randint(2, 3)))
            out.append((grid, pattern))
    elif name == "py_word_ladder":
        for _ in range(25):
            pool = ["".join(rng.choice("abc") for _ in range(3)) for _ in range(rng.randint(3, 12))]
            start, end = "".join(rng.choice("abc") for _ in range(3)), rng.choice(pool)
            if start != end:
                out.append((start, end, pool))
    elif name == "redundant_link":
        out = [(_tree_edges(rng, rng.randint(3, 9)),) for _ in range(25)]
    elif name == "task_order":
        for _ in range(30):
            n = rng.randint(1, 8)
            pairs = []
            for a in range(n):
                for b in range(n):
                    if a != b and rng.random() < 0.15 and [a, b] not in pairs:
                        pairs.append([a, b])
            out.append((n, pairs))
    elif name == "trie_autocomplete":
        for _ in range(25):
            words = ["".join(rng.choice("abcA") for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(0, 10))]
            prefix = "".join(rng.choice("abA") for _ in range(rng.randint(0, 2)))
            out.append((words, prefix))
    elif name == "bridge_finder":
        out = [(_undirected(rng, rng.randint(1, 8), rng.choice([0.2, 0.35, 0.5])),) for _ in range(30)]
    elif name == "pack_strings":
        alphabet = "ab#:0123 \n,"
        out = [(["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8))) for _ in range(rng.randint(0, 5))],)
               for _ in range(30)]
    return out


def random_cases(name, rng):
    """Random cases for `name`. Call subjects get ('fname', args) pairs or args tuples."""
    return _random_rank03(name, rng) or _random_new(name, rng)


# ── class subjects: random operation scripts ────────────────────────────────
def class_cases(name, rng):
    """[(constructor args, [(method, args)])]"""
    cases = []
    if name == "prefix_dictionary":
        words = ["a", "ab", "abc", "app", "apple", "apply", "b", "bat", "bath", "cat", "car"]
        cases += [((), [("search", ("",)), ("starts_with", ("",))]),
                  ((), [("insert", ("",)), ("search", ("",)), ("starts_with", ("a",))]),
                  ((), [("insert", ("apple",)), ("insert", ("apple",)), ("search", ("apple",)),
                        ("search", ("apples",)), ("starts_with", ("apples",))])]
        for _ in range(25):
            ops = []
            for _ in range(rng.randint(2, 12)):
                kind = rng.choice(["insert", "insert", "search", "starts_with"])
                word = rng.choice(words)
                if kind != "insert" and rng.random() < 0.4:
                    word = word[:rng.randint(0, len(word))]
                ops.append((kind, (word,)))
            cases.append(((), ops))
    elif name == "union_find_system":
        cases += [((1,), [("connected", (0, 0)), ("union", (0, 0))]),
                  ((4,), [("union", (0, 1)), ("union", (2, 3)), ("union", (1, 3)), ("connected", (0, 2)),
                          ("__same_root__", (0, 3)), ("union", (3, 0))])]
        for _ in range(25):
            n = rng.randint(2, 10)
            ops = []
            for _ in range(rng.randint(3, 15)):
                kind = rng.choice(["union", "union", "connected", "__same_root__"])
                ops.append((kind, (rng.randrange(n), rng.randrange(n))))
            cases.append(((n,), ops))
    elif name == "cache_keeper":
        cases += [((1,), [("put", (1, 1)), ("put", (2, 2)), ("get", (1,)), ("get", (2,))]),
                  ((2,), [("put", (1, 1)), ("put", (1, 10)), ("get", (1,)), ("put", (2, 2)), ("put", (3, 3)),
                          ("get", (1,)), ("get", (2,)), ("get", (3,))]),
                  ((2,), [("get", (5,))])]
        for _ in range(25):
            cap = rng.randint(1, 4)
            ops = []
            for _ in range(rng.randint(3, 16)):
                if rng.random() < 0.5:
                    ops.append(("put", (rng.randint(1, 6), rng.randint(0, 99))))
                else:
                    ops.append(("get", (rng.randint(1, 6),)))
            cases.append(((cap,), ops))
    elif name == "min_heap":
        cases += [((), [("peek", ()), ("size", ())]),
                  ((), [("push", (1,)), ("pop", ()), ("pop", ()), ("size", ())]),
                  ((), [("push", (2,)), ("push", (2,)), ("push", (1,)), ("pop", ()), ("pop", ()), ("pop", ()),
                        ("peek", ())]),
                  ((), [("push", (-5,)), ("push", (0,)), ("push", (-10,)), ("peek", ()), ("size", ())])]
        for _ in range(25):
            ops = []
            for _ in range(rng.randint(3, 20)):
                r = rng.random()
                if r < 0.55:
                    ops.append(("push", (rng.randint(-20, 20),)))
                elif r < 0.8:
                    ops.append(("pop", ()))
                elif r < 0.9:
                    ops.append(("peek", ()))
                else:
                    ops.append(("size", ()))
            cases.append(((), ops))
    return cases


# ── ambiguous subjects: other readings that must agree ──────────────────────
def _resolver_fifo(packages):
    """Kahn with a FIFO queue (sorted start, dependents in sorted order)."""
    deps = {p: {d for d in ds if d in packages} for p, ds in packages.items()}
    if any(p in d for p, d in deps.items()):
        return []
    users = {p: [] for p in deps}
    for p, ds in deps.items():
        for d in ds:
            users[d].append(p)
    waiting = {p: len(ds) for p, ds in deps.items()}
    queue = sorted(p for p in deps if not waiting[p])
    order = []
    while queue:
        p = queue.pop(0)
        order.append(p)
        for u in sorted(users[p]):
            waiting[u] -= 1
            if not waiting[u]:
                queue.append(u)
    return order if len(order) == len(deps) else []


def _rooms(meetings, earliest=False, strict=False):
    rooms = []
    for s, e in sorted(meetings, key=lambda m: m[0]):
        free = [r for r in rooms if (r[-1][1] < s if strict else r[-1][1] <= s)]
        if free:
            room = min(free, key=lambda r: r[-1][1]) if earliest else free[0]
            room.append([s, e])
        else:
            rooms.append([[s, e]])
    return {"total_rooms": len(rooms), "schedule": rooms}


def _prism_swapped(grid, pattern):
    """D2 read as up-right (1, -1), the way its label says."""
    dirs = (((1, 0), "H"), ((-1, 0), "H-"), ((0, 1), "V"), ((0, -1), "V-"),
            ((1, 1), "D1"), ((-1, -1), "D1-"), ((1, -1), "D2"), ((-1, 1), "D2-"))
    if not grid or not pattern:
        return []
    found = []
    for y, row in enumerate(grid):
        for x in range(len(row)):
            for (dx, dy), code in dirs:
                if all(0 <= y + dy * i < len(grid) and 0 <= x + dx * i < len(grid[y + dy * i])
                       and grid[y + dy * i][x + dx * i] == c for i, c in enumerate(pattern)):
                    found.append((x, y, code))
    return found


ALTERNATES = {
    "py_package_dependency_resolver": [_resolver_fifo],
    "py_room_scheduler": [lambda m: _rooms(m, earliest=True), lambda m: _rooms(m, strict=True)],
    "py_prism_detector": [_prism_swapped],
}


# ── speed checks: subjects that ask for a complexity ────────────────────────
# (description, kind, function or class name, builder source). The builder is
# copied into tests.py, so it must be self-contained: def build(rng): ...
PERF = {
    "py_sliding_window_maximum": [(
        "200 000 numbers, window of 5 000", "call", "sliding_window_maximum",
        "def build(rng):\n"
        "    return ([rng.randint(-10**6, 10**6) for _ in range(200000)], 5000)\n")],
    "py_merge_sorted_lists": [(
        "2 000 lists, 200 000 numbers", "call", "merge_sorted_lists",
        "def build(rng):\n"
        "    out = []\n"
        "    for _ in range(2000):\n"
        "        x, lst = rng.randint(-10**6, 0), []\n"
        "        for _ in range(100):\n"
        "            x += rng.randint(0, 50)\n"
        "            lst.append(x)\n"
        "        out.append(lst)\n"
        "    return (out,)\n")],
    "py_palindrome_partitioner": [(
        "a 200-character string", "call", "palindrome_partitioner",
        "def build(rng):\n"
        "    return (''.join(rng.choice('ab') for _ in range(200)),)\n")],
    "cache_keeper": [(
        "200 000 operations, capacity 50 000", "class", "CacheKeeper",
        "def build(rng):\n"
        "    ops = []\n"
        "    for _ in range(200000):\n"
        "        if rng.random() < 0.5:\n"
        "            ops.append(('put', (rng.randint(0, 100000), rng.randint(0, 9))))\n"
        "        else:\n"
        "            ops.append(('get', (rng.randint(0, 100000),)))\n"
        "    return ((50000,), ops)\n")],
    "min_heap": [(
        "100 000 pushes then 100 000 pops", "class", "MinHeap",
        "def build(rng):\n"
        "    ops = [('push', (rng.randint(-10**6, 10**6),)) for _ in range(100000)]\n"
        "    ops += [('pop', ())] * 100000\n"
        "    return ((), ops)\n")],
    "union_find_system": [(
        "200 000 unions and checks on 100 000 elements", "class", "UnionFind",
        "def build(rng):\n"
        "    n = 100000\n"
        "    ops = [('union', (i, i + 1)) for i in range(n - 1)]\n"
        "    ops += [('connected', (rng.randrange(n), rng.randrange(n))) for _ in range(100000)]\n"
        "    return ((n,), ops)\n")],
}

# forbidden lists the data lost but the subject text still states
FORBIDDEN = {
    "py_cryptic_sorter": ["sorted()", ".sort()"],
}
