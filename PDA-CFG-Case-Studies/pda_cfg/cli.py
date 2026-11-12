"""Command-line tool.
  python -m pda_cfg.cli ambiguity            bounded ambiguity check (parse-tree counts)
  python -m pda_cfg.cli expr [string]        test strings: CFG / PDA / LL(1) / trees
  python -m pda_cfg.cli brackets "<source>"  DPDA syntax check with the accepting computation
  python -m pda_cfg.cli palindromes          wcw^R (DPDA) and ww^R (NPDA)"""
import sys
from . import cases as c
from .pda import brackets_dpda, wcwr_dpda, wwr_npda


def ambiguity():
    print("=" * 74)
    print("Bounded ambiguity check (count parse trees of every short string)")
    print("=" * 74)
    jobs = [(c.BRACKETS_AMBIGUOUS, 8), (c.BRACKETS_FIXED, 8), (c.EXPR_AMBIGUOUS, 7),
            (c.EXPR_PRECEDENCE, 7), (c.EXPR_LL1, 7), (c.PALINDROMES, 8)]
    for g, n in jobs:
        strings = [s for s in g.generate(n)]
        multi = [(s, g.count_trees(s)) for s in strings if g.count_trees(s) > 1]
        verdict = "AMBIGUOUS" if multi else "no ambiguity found"
        ex = ""
        if multi:
            s, k = max(multi, key=lambda t: t[1])
            ex = f" e.g. '{' '.join(s)}' has {k} trees"
        print(f"{g.name:38} strings <={n}: {len(strings):5}  with >1 tree: {len(multi):4}  {verdict}{ex}")
    print("(CFG ambiguity is undecidable in general; this is evidence, not a proof)")


def expr(strings=None):
    strings = strings or ["id", "id+id*id", "(id+id)*id", "id*(id+id)*id", "((id))", "id+id+id",
                          "", "id+", "+id", "id id", "(id+id", "id*)id(", "id+*id"]
    pda = c.EXPR_PRECEDENCE.to_pda()
    print(f"{'input':16}{'CFG':8}{'PDA':8}{'LL(1)':8}trees in ambiguous G")
    for s in strings:
        t = c.tokens_of_expr(s)
        if t is None:
            print(f"{s!r:16}REJECT (bad character)"); continue
        r = lambda b: "ACCEPT" if b else "REJECT"
        print(f"{s!r:16}{r(c.EXPR_PRECEDENCE.generates(t)):8}{r(pda.accepts(t)):8}"
              f"{r(c.EXPR_LL1.ll1_parse(t)):8}{c.EXPR_AMBIGUOUS.count_trees(t)}")
    t = ["id", "+", "id", "*", "id"]
    ok, n, _ = pda.search(t)
    print(f"\nCFG->PDA is deterministic: {pda.is_deterministic()}; choice points: {c.EXPR_PRECEDENCE.choice_points()}")
    print(f"configurations explored to accept id+id*id: {n}")
    for k, d in enumerate(c.EXPR_AMBIGUOUS.leftmost_derivations(t), 1):
        print(f"LMD {k}: " + " => ".join(" ".join(f) for f in d))


def brackets(source):
    pda = brackets_dpda()
    only = c.brackets_only(source)
    ids, verdict = pda.explain(only)
    print(f"brackets kept: {only!r}")
    print(" |- ".join(ids))
    print(verdict.upper(), "| DPDA:", pda.is_deterministic())


def palindromes():
    for pda, words in [(wcwr_dpda(), ["c", "aca", "abcba", "abbcbba", "", "ab", "abcab", "abcbaa"]),
                       (wwr_npda(), ["", "aa", "abba", "baab", "a", "ab", "aba", "abab"])]:
        print(f"{pda.name}: deterministic = {pda.is_deterministic()}")
        for w in words:
            print(f"   {w!r:10} {'ACCEPT' if pda.accepts(w) else 'REJECT'}")


def main(a):
    if a[:1] == ["ambiguity"]: return ambiguity()
    if a[:1] == ["expr"]: return expr(a[1:])
    if a[:1] == ["brackets"] and len(a) == 2: return brackets(a[1])
    if a[:1] == ["palindromes"]: return palindromes()
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
