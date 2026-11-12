"""The three case studies: grammars, helpers, lexer and evaluators."""
import random
from .cfg import CFG
from .pda import brackets_dpda, wcwr_dpda, wwr_npda

BRACKETS_AMBIGUOUS = CFG("Balanced brackets (ambiguous)", "S -> S S | ( S ) | [ S ] | { S } | ( ) | [ ] | { }")
BRACKETS_FIXED = CFG("Balanced brackets (unambiguous)", """
S -> B S | B
B -> ( S ) | ( ) | [ S ] | [ ] | { S } | { }""")
EXPR_AMBIGUOUS = CFG("Expressions (ambiguous)", "E -> E + E | E * E | ( E ) | id")
EXPR_PRECEDENCE = CFG("Expressions (precedence grammar)", """
E -> E + T | T
T -> T * F | F
F -> ( E ) | id""")
EXPR_LL1 = CFG("Expressions (LL(1) form)", """
E -> T R
R -> + T R | eps
T -> F U
U -> * F U | eps
F -> ( E ) | id""")
PALINDROMES = CFG("All palindromes over {a,b}", "S -> a S a | b S b | a | b | eps")
WCWR = CFG("w c w^R", "S -> a S a | b S b | c")


def tokens_of_expr(text):
    """'id+id*id' or 'id + id * id' -> ['id','+','id','*','id'] (None if a stray character appears)."""
    out, i = [], 0
    text = text.replace(" ", "")
    while i < len(text):
        if text.startswith("id", i):
            out.append("id"); i += 2
        elif text[i] in "+*()":
            out.append(text[i]); i += 1
        else:
            return None
    return out


def brackets_only(source):
    """Lexer: keep only brackets of a source line and skip string literals."""
    out, i, quote = [], 0, None
    while i < len(source):
        c = source[i]
        if quote:
            if c == "\\":
                i += 1
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in "()[]{}":
            out.append(c)
        i += 1
    return "".join(out)


def check_syntax(source):
    return brackets_dpda().accepts(brackets_only(source))


def evaluate_expr(tokens, values):
    """Recursive descent for the precedence grammar; ids take successive values from `values`.
    Returns None for strings the grammar rejects."""
    vals, pos, i = list(values), [0], [0]
    def peek(): return tokens[pos[0]] if pos[0] < len(tokens) else None
    def eat(): pos[0] += 1; return tokens[pos[0] - 1]
    class Bad(Exception): pass
    def F():
        t = peek()
        if t == "id":
            eat(); v = vals[i[0] % len(vals)]; i[0] += 1; return v
        if t == "(":
            eat(); v = E()
            if peek() != ")": raise Bad
            eat(); return v
        raise Bad
    def T_():
        v = F()
        while peek() == "*":
            eat(); v *= F()
        return v
    def E():
        v = T_()
        while peek() == "+":
            eat(); v += T_()
        return v
    try:
        v = E()
        return v if pos[0] == len(tokens) else None
    except Bad:
        return None


def random_expression(rnd, depth=3):
    """A random valid expression as a token list."""
    if depth == 0 or rnd.random() < 0.3:
        return ["id"]
    if rnd.random() < 0.25:
        return ["("] + random_expression(rnd, depth - 1) + [")"]
    return random_expression(rnd, depth - 1) + [rnd.choice("+*")] + random_expression(rnd, depth - 1)


def mutate(rnd, toks):
    toks = list(toks)
    k = rnd.choice(["drop", "insert", "swap"])
    pool = ["id", "+", "*", "(", ")"]
    if k == "drop" and toks:
        del toks[rnd.randrange(len(toks))]
    elif k == "insert":
        toks.insert(rnd.randrange(len(toks) + 1), rnd.choice(pool))
    elif toks:
        toks[rnd.randrange(len(toks))] = rnd.choice(pool)
    return toks
