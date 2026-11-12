import ast, itertools, random, unittest
from pda_cfg import cases as c
from pda_cfg.pda import brackets_dpda, wcwr_dpda, wwr_npda


def strings(alpha, n):
    for k in range(n + 1):
        for t in itertools.product(alpha, repeat=k):
            yield "".join(t)


def balanced(s):                       # independent checker (counter-free stack of expected closers)
    stack = []
    for ch in s:
        if ch in "([{": stack.append({"(": ")", "[": "]", "{": "}"}[ch])
        elif not stack or stack.pop() != ch: return False
    return not stack


class TestBrackets(unittest.TestCase):
    def test_table3_examples(self):
        for s in ["()", "[]{}", "([]{})", "{[()()]}", "(((())))", "()[]{}([])"]:
            self.assertTrue(brackets_dpda().accepts(s), s)
            self.assertTrue(c.BRACKETS_FIXED.generates(tuple(s)), s)
        for s in ["(", ")(", "([)]", "(()", "{]}", "())(()"]:
            self.assertFalse(brackets_dpda().accepts(s), s)
            self.assertFalse(c.BRACKETS_FIXED.generates(tuple(s)), s)

    def test_all_5461_strings_up_to_length_6(self):
        d, n = brackets_dpda(), 0
        for s in strings("()[]", 6):
            n += 1
            self.assertEqual(d.accepts(s), balanced(s) and s != "", s)
        self.assertEqual(n, 5461)

    def test_is_dpda(self):
        self.assertTrue(brackets_dpda().is_deterministic())

    def test_ambiguity_counts(self):
        self.assertEqual(c.BRACKETS_AMBIGUOUS.count_trees(tuple("()()()")), 2)
        self.assertEqual(c.BRACKETS_AMBIGUOUS.count_trees(tuple("()()()()")), 5)
        self.assertEqual(c.BRACKETS_FIXED.count_trees(tuple("()()()()")), 1)

    def test_both_grammars_generate_same_language(self):
        self.assertEqual(c.BRACKETS_AMBIGUOUS.generate(8), c.BRACKETS_FIXED.generate(8))
        self.assertEqual(len(c.BRACKETS_FIXED.generate(8)), 1290)

    def test_lexer_and_syntax_checker(self):
        self.assertTrue(c.check_syntax("if (a[i] > 0) { sum += f(a[i]); }"))
        self.assertFalse(c.check_syntax("x = (a + b];"))
        self.assertTrue(c.check_syntax('print("(((", x)'))          # brackets inside strings are skipped
        self.assertEqual(c.brackets_only("a['k'] = {1}"), "[]{}")


class TestExpressions(unittest.TestCase):
    GOOD = ["id", "id+id*id", "(id+id)*id", "id*(id+id)*id", "((id))", "id+id+id"]
    BAD = ["", "id+", "+id", "id id", "(id+id", "id*)id(", "id+*id"]

    def test_examples_agree_everywhere(self):
        pda = c.EXPR_PRECEDENCE.to_pda()
        for s, want in [(g, True) for g in self.GOOD] + [(b, False) for b in self.BAD]:
            t = c.tokens_of_expr(s)
            self.assertEqual(c.EXPR_PRECEDENCE.generates(t), want, s)
            self.assertEqual(pda.accepts(t), want, s)
            self.assertEqual(c.EXPR_LL1.ll1_parse(t), want, s)
            self.assertEqual(c.EXPR_AMBIGUOUS.generates(t), want, s)

    def test_ambiguous_grammar_has_two_trees_for_id_plus_id_times_id(self):
        t = ["id", "+", "id", "*", "id"]
        self.assertEqual(c.EXPR_AMBIGUOUS.count_trees(t), 2)
        self.assertEqual(c.EXPR_PRECEDENCE.count_trees(t), 1)
        self.assertEqual(len(c.EXPR_AMBIGUOUS.leftmost_derivations(t)), 2)

    def test_values_14_and_20(self):
        self.assertEqual(c.evaluate_expr(["id", "+", "id", "*", "id"], [2, 3, 4]), 14)   # precedence tree
        self.assertEqual((2 + 3) * 4, 20)                                                # the other tree

    def test_cfg_to_pda_is_nondeterministic_with_three_choice_points(self):
        pda = c.EXPR_PRECEDENCE.to_pda()
        self.assertFalse(pda.is_deterministic())
        self.assertEqual(c.EXPR_PRECEDENCE.choice_points(), ["E", "F", "T"])

    def test_ll1_grammar_has_no_conflicts_and_left_recursive_does_not(self):
        self.assertEqual(c.EXPR_LL1.ll1_table()[1], [])
        self.assertTrue(c.EXPR_PRECEDENCE.ll1_table()[1])

    def test_1500_random_expressions_against_python(self):
        rnd, pda = random.Random(2026), c.EXPR_PRECEDENCE.to_pda()
        for _ in range(1500):
            t = c.random_expression(rnd)
            if rnd.random() < 0.5:
                t = c.mutate(rnd, t)
            vals = [rnd.randint(1, 9) for _ in range(len(t))]
            # independent oracle: Python's own parser, ids replaced by numbers, no unary operators
            it = iter(vals)
            src = " ".join(str(next(it)) if x == "id" else x for x in t)
            try:
                tree = ast.parse(src, mode="eval")
                ok = all(isinstance(n, (ast.Expression, ast.BinOp, ast.Constant, ast.Add, ast.Mult, ast.Load))
                         for n in ast.walk(tree)) and "**" not in src
                py = eval(compile(tree, "", "eval")) if ok else None
            except SyntaxError:
                ok, py = False, None
            self.assertEqual(c.EXPR_PRECEDENCE.generates(t), ok, src)
            self.assertEqual(c.EXPR_LL1.ll1_parse(t), ok, src)
            self.assertEqual(pda.accepts(t), ok, src)
            if ok:
                self.assertEqual(c.evaluate_expr(t, vals), py, src)


class TestPalindromes(unittest.TestCase):
    def test_table3_examples(self):
        for s in ["c", "aca", "abcba", "abbcbba", "babcbab", "aabacabaa"]:
            self.assertTrue(wcwr_dpda().accepts(s), s)
        for s in ["", "ab", "abcab", "abcb", "acca", "abcbaa"]:
            self.assertFalse(wcwr_dpda().accepts(s), s)
        for s in ["", "aa", "abba", "baab", "abbbba", "aabbaabbaa"]:
            self.assertTrue(wwr_npda().accepts(s), s)
        for s in ["a", "ab", "aba", "abab", "aabb", "abbaa"]:
            self.assertFalse(wwr_npda().accepts(s), s)

    def test_determinism(self):
        self.assertTrue(wcwr_dpda().is_deterministic())
        self.assertFalse(wwr_npda().is_deterministic())

    def test_all_511_strings_up_to_length_8_ww_r(self):
        n = 0
        for s in strings("ab", 8):
            n += 1
            self.assertEqual(wwr_npda().accepts(s), len(s) % 2 == 0 and s == s[::-1], s)
        self.assertEqual(n, 511)

    def test_wcwr_exhaustive(self):
        for s in strings("abc", 9):
            want = s.count("c") == 1 and s.split("c")[0] == s.split("c")[1][::-1]
            self.assertEqual(wcwr_dpda().accepts(s), want, s)

    def test_cfg_generates_all_palindromes_and_is_unambiguous(self):
        pals = c.PALINDROMES.generate(8)
        self.assertEqual(len(pals), 61)
        for w in pals:
            self.assertEqual("".join(w), "".join(w)[::-1])
            self.assertEqual(c.PALINDROMES.count_trees(w), 1)
        self.assertEqual(len(c.WCWR.generate(9)), 2 ** 4 + 2 ** 3 + 2 ** 2 + 2 + 1)


if __name__ == "__main__":
    unittest.main()
