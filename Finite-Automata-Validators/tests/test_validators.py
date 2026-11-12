"""Each automaton is compared with an independently written Python rule."""
import itertools, random, re, string, unittest
from fa_validators import validators as v
from fa_validators.automata import DFA, NFA, subset_construction, minimise
from fa_validators.cli import SAMPLES, APPS, _symbols


def all_strings(alphabet, max_len):
    for n in range(max_len + 1):
        for t in itertools.product(alphabet, repeat=n):
            yield "".join(t)


class TestPin(unittest.TestCase):
    def test_examples(self):
        good, bad = SAMPLES["pin"]
        for s in good: self.assertTrue(v.validate_pin(s), s)
        for s in bad: self.assertFalse(v.validate_pin(s), s)

    def test_exhaustive_short_strings(self):
        n = 0
        for s in all_strings("019x", 6):
            n += 1
            self.assertEqual(v.validate_pin(s), len(s) == 4 and s.isdigit(), s)
        self.assertEqual(n, 5461)

    def test_size(self):
        self.assertEqual(v.pin_dfa().size()[1], 5)

    def test_weak_pin_all_10000(self):
        for i in range(10000):
            s = f"{i:04d}"
            self.assertEqual(v.validate_weak_pin(s), len(set(s)) > 1, s)

    def test_weak_pin_other_lengths_and_chars(self):
        for s in ["", "123", "12345", "1a34", "1111", "11111"]:
            self.assertFalse(v.validate_weak_pin(s), s)

    def test_weak_pin_size(self):
        self.assertEqual(v.weak_pin_dfa().size()[1], 34)


class TestCardLock(unittest.TestCase):
    def test_examples(self):
        good, bad = SAMPLES["card"]
        for s in good: self.assertTrue(v.validate_card_events(s), s)
        for s in bad: self.assertFalse(v.validate_card_events(s), s)

    def test_exhaustive(self):
        for s in all_strings("CW", 10):
            self.assertEqual(v.validate_card_events(s), re.match(r"W{0,2}C", s) is not None, s)


class TestPassword(unittest.TestCase):
    @staticmethod
    def rule(p):
        return (8 <= len(p) <= 16 and all(c in string.printable[:94] for c in p)
                and any(c.isupper() for c in p) and any(c.islower() for c in p)
                and any(c.isdigit() for c in p) and any(c in string.punctuation for c in p))

    def test_examples(self):
        good, bad = SAMPLES["password"]
        for s in good: self.assertTrue(v.validate_password(s), s)
        for s in bad: self.assertFalse(v.validate_password(s), s)

    def test_20000_random(self):
        rnd = random.Random(2026)
        pool = string.ascii_letters + string.digits + string.punctuation + " é"
        for _ in range(20000):
            n = rnd.randint(0, 18)
            p = "".join(rnd.choice(pool) for _ in range(n))
            self.assertEqual(v.validate_password(p), self.rule(p), p)

    def test_guaranteed_valid_random(self):
        rnd = random.Random(7)
        for _ in range(2000):
            n = rnd.randint(8, 16)
            p = [rnd.choice(string.ascii_uppercase), rnd.choice(string.ascii_lowercase),
                 rnd.choice(string.digits), rnd.choice(string.punctuation)]
            p += [rnd.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(n - 4)]
            rnd.shuffle(p)
            self.assertTrue(v.validate_password("".join(p)))

    def test_sizes(self):
        self.assertEqual(sum([2, 2, 2, 2, 17]), 25)
        self.assertEqual(v.password_product().size()[0], 225)       # 224 live + trap
        self.assertEqual(v.password_minimal().size()[1], 196)       # live states of the minimal DFA

    def test_minimal_equals_product(self):
        prod, mini = v.password_product(), v.password_minimal()
        rnd = random.Random(1)
        for _ in range(3000):
            s = [rnd.choice("ULDSO") for _ in range(rnd.randint(0, 18))]
            self.assertEqual(prod.accepts_symbols(s), mini.accepts_symbols(s))

    def test_product_equals_five_components(self):
        comps, prod = v.password_components(), v.password_product()
        rnd = random.Random(3)
        for _ in range(3000):
            s = [rnd.choice("ULDSO") for _ in range(rnd.randint(0, 18))]
            self.assertEqual(all(c.accepts_symbols(s) for c in comps), prod.accepts_symbols(s))


EMAIL_RE = re.compile(r"[A-Za-z0-9]+([._-][A-Za-z0-9]+)*@[A-Za-z0-9]+(-+[A-Za-z0-9]+)*"
                      r"(\.[A-Za-z0-9]+(-+[A-Za-z0-9]+)*)*\.[A-Za-z]{2,}")


class TestEmail(unittest.TestCase):
    def test_examples(self):
        good, bad = SAMPLES["email"]
        for s in good: self.assertTrue(v.validate_email(s), s)
        for s in bad: self.assertFalse(v.validate_email(s), s)

    def test_all_335923_strings_up_to_length_7(self):
        n = 0
        for s in all_strings("a1.-_@", 7):
            n += 1
            self.assertEqual(v.validate_email(s), EMAIL_RE.fullmatch(s) is not None, s)
        self.assertEqual(n, 335923)

    def test_sizes(self):
        self.assertEqual(len(v.email_nfa().states()), 9)
        self.assertEqual(v.email_subset_dfa().size()[1], 9)
        self.assertEqual(v.email_minimal().size()[1], 8)

    def test_nfa_dfa_minimal_agree(self):
        nfa, sub, mini = v.email_nfa(), v.email_subset_dfa(), v.email_minimal()
        rnd = random.Random(5)
        for _ in range(5000):
            s = [rnd.choice(["L", "D", "DOT", "HY", "US", "AT", "O"]) for _ in range(rnd.randint(0, 14))]
            self.assertEqual(nfa.accepts_symbols(s), sub.accepts_symbols(s))
            self.assertEqual(sub.accepts_symbols(s), mini.accepts_symbols(s))

    def test_minimisation_merges_n0_and_n2(self):
        sub = v.email_subset_dfa()
        a, b = frozenset({"n0"}), frozenset({"n2"})
        for sym in sub.alphabet:
            ra, rb = sub.step(a, sym), sub.step(b, sym)
            self.assertEqual(ra, rb)


class TestLibrary(unittest.TestCase):
    def test_every_automaton_is_complete_and_trace_runs(self):
        for app, (good, bad) in SAMPLES.items():
            dfa = APPS[app][0]()
            for s in good + bad:
                rows, final = dfa.trace(_symbols(app, s), list(s))
                self.assertEqual(len(rows), len(s))
                self.assertEqual(final in dfa.accepts, dfa.accepts_symbols(_symbols(app, s)))

    def test_subset_construction_small_example(self):   # strings over {a,b} whose 2nd-last symbol is a
        nfa = NFA("2nd-last a", "ab", {("p", "a"): {"p", "q"}, ("p", "b"): {"p"},
                                         ("q", "a"): {"r"}, ("q", "b"): {"r"}}, "p", {"r"})
        dfa = minimise(subset_construction(nfa))
        for s in all_strings("ab", 8):
            self.assertEqual(dfa.accepts_symbols(s), len(s) >= 2 and s[-2] == "a")
        self.assertEqual(dfa.size()[1], 4)


if __name__ == "__main__":
    unittest.main()
