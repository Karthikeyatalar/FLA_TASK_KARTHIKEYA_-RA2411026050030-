"""The three validators: ATM PIN (+ card lock), password policy and e-mail format."""
import string
from .automata import DFA, NFA, subset_construction, product, minimise

DIGITS = "0123456789"


# ---------- character classifiers (the automata read classes, not raw characters) ----------
def classify_pin(ch):
    return "D" if ch in DIGITS else "O"


def classify_password(ch):
    if ch in string.ascii_uppercase:
        return "U"
    if ch in string.ascii_lowercase:
        return "L"
    if ch in DIGITS:
        return "D"
    if ch in string.punctuation:
        return "S"
    return "O"


def classify_email(ch):
    if ch in string.ascii_letters:
        return "L"
    if ch in DIGITS:
        return "D"
    return {".": "DOT", "-": "HY", "_": "US", "@": "AT"}.get(ch, "O")


# ---------- Application 1: ATM PIN and card lock ----------
def pin_dfa():
    """L_PIN = { w in D* : |w| = 4 }; q0..q4 count digits, q4 accepts."""
    delta = {(f"q{i}", "D"): f"q{i+1}" for i in range(4)}
    return DFA("ATM PIN (4 digits)", "DO", delta, "q0", {"q4"})


def weak_pin_dfa():
    """4 digits, not all equal. Needs the raw alphabet 0-9."""
    delta = {("q0", d): f"e1_{d}" for d in DIGITS}
    for d in DIGITS:
        for e in DIGITS:
            delta[(f"e1_{d}", e)] = f"e2_{d}" if e == d else "mix2"
            delta[(f"e2_{d}", e)] = f"e3_{d}" if e == d else "mix3"
            if e != d:
                delta[(f"e3_{d}", e)] = "ok"      # e3_d --d--> trap (four equal digits)
    for e in DIGITS:
        delta[("mix2", e)] = "mix3"
        delta[("mix3", e)] = "ok"
    return DFA("PIN, not all digits equal", DIGITS, delta, "q0", {"ok"})


def card_lock_dfa():
    """Events C (correct PIN) / W (wrong PIN). Three consecutive W lock the card."""
    delta = {("s0", "W"): "s1", ("s1", "W"): "s2", ("s2", "W"): "LOCK",
             ("s0", "C"): "AUTH", ("s1", "C"): "AUTH", ("s2", "C"): "AUTH",
             ("AUTH", "C"): "AUTH", ("AUTH", "W"): "AUTH",
             ("LOCK", "C"): "LOCK", ("LOCK", "W"): "LOCK"}
    return DFA("Card lock (events C/W)", "CW", delta, "s0", {"AUTH"})


# ---------- Application 2: password policy ----------
def _contains(cls):
    delta = {("no", a): "no" for a in "ULDSO"}
    delta.update({("yes", a): "yes" for a in "ULDSO"})
    delta[("no", cls)] = "yes"
    return DFA(f"contains {cls}", "ULDSO", delta, "no", {"yes"})


def _length(lo=8, hi=16):
    delta = {(f"l{i}", a): f"l{i+1}" for i in range(hi) for a in "ULDS"}   # 'O' -> trap
    return DFA(f"length {lo}-{hi}", "ULDSO", delta, "l0", {f"l{i}" for i in range(lo, hi + 1)})


def password_components():
    return [_contains("U"), _contains("L"), _contains("D"), _contains("S"), _length()]


def password_product():
    return product(password_components(), "Password policy (product)")


def password_minimal():
    return minimise(password_product(), prefix="p", name="Password policy (minimal)")


# ---------- Application 3: e-mail format ----------
def email_nfa():
    """local = alnum+([._-]alnum+)* '@' label ('.' label)* '.' TLD ; TLD = 2+ letters.
    n4 --'.'--> n3 (another label) or n6 (TLD starts here): this is the guess."""
    d = {}

    def add(q, syms, r):
        for s in syms.split():
            d.setdefault((q, s), set()).add(r)

    add("n0", "L D", "n1"); add("n1", "L D", "n1"); add("n1", "DOT HY US", "n2")
    add("n2", "L D", "n1"); add("n1", "AT", "n3"); add("n3", "L D", "n4")
    add("n4", "L D", "n4"); add("n4", "DOT", "n3"); add("n4", "HY", "n5")
    add("n5", "HY", "n5"); add("n5", "L D", "n4"); add("n4", "DOT", "n6")
    add("n6", "L", "n7"); add("n7", "L", "n8"); add("n8", "L", "n8")
    return NFA("E-mail format (NFA)", ["L", "D", "DOT", "HY", "US", "AT", "O"], d, "n0", {"n8"})


def email_subset_dfa():
    return subset_construction(email_nfa())


def email_minimal():
    return minimise(email_subset_dfa(), prefix="m", name="E-mail format (minimal DFA)")


# ---------- public helpers ----------
def _classes(text, classifier):
    return [classifier(c) for c in text]


def validate_pin(text):
    return pin_dfa().accepts_symbols(_classes(text, classify_pin))


def validate_weak_pin(text):
    return weak_pin_dfa().accepts_symbols(list(text) if all(c in DIGITS for c in text) else ["x"])


def validate_card_events(events):
    return card_lock_dfa().accepts_symbols(list(events))


_PW = None
_EM = None


def validate_password(text):
    global _PW
    _PW = _PW or password_minimal()
    return _PW.accepts_symbols(_classes(text, classify_password))


def validate_email(text):
    global _EM
    _EM = _EM or email_minimal()
    return _EM.accepts_symbols(_classes(text, classify_email))
