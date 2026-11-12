"""Command-line demo.
  python -m fa_validators.cli <pin|card|password|email> <text>   step-by-step trace
  python -m fa_validators.cli table                              accept/reject tables
  python -m fa_validators.cli sizes                              state counts"""
import sys
from . import validators as v

APPS = {
    "pin": (v.pin_dfa, v.classify_pin),
    "card": (v.card_lock_dfa, None),
    "password": (v.password_minimal, v.classify_password),
    "email": (v.email_minimal, v.classify_email),
}
SAMPLES = {
    "pin": (["4821", "0000", "9375", "1234", "0042", "7777"], ["482", "48211", "48a1", "12 34", "", "-123", "4,821"]),
    "card": (["C", "WC", "WWC", "CW", "WWCWW"], ["", "W", "WW", "WWW", "WWWC", "WWWWC"]),
    "password": (["Srm@2026", "Trichy#Aiml5", "aB3$efgh", "P@ssw0rdX", "Q1w2e3r4!T", "Zz9_Zz9_Zz9_Zz9_"],
                 ["srm@2026", "SRM@2026", "Srm@Trichy", "Srm20266", "Sr@1", "Srm @2026", "Abcdefgh1!xyzABC9"]),
    "email": (["vaishak.kr@srmist.edu.in", "ra2411026050018@srmist.edu.in", "srm_student@gmail.com",
               "a-b.c@my-site.co", "x@y.io"],
              ["vaishak@srmist", ".vaishak@gmail.com", "vaishak..kr@gmail.com", "vaishak@-srm.in",
               "vaishak@srm.c0m", "vaishak@@gmail.com"]),
}


def _symbols(app, text):
    classifier = APPS[app][1]
    return [classifier(c) for c in text] if classifier else list(text)


def show(app, text):
    dfa = APPS[app][0]()
    rows, final = dfa.trace(_symbols(app, text), list(text))
    print(f"{dfa.name} on {text!r}")
    for i, q, ch, s, r in rows:
        print(f"  {i:2}. d({q}, {ch!r} -> {s}) = {r}")
    print(f"  final state {final} -> {'ACCEPTED' if final in dfa.accepts else 'REJECTED'}")


def table():
    for app, (good, bad) in SAMPLES.items():
        dfa = APPS[app][0]()
        print(f"\n== {app} ==")
        for s in good + bad:
            print(f"  {s!r:34} {'ACCEPT' if dfa.accepts_symbols(_symbols(app, s)) else 'REJECT'}")


def sizes():
    comps = v.password_components()
    print("PIN DFA live states:", v.pin_dfa().size()[1])
    print("Weak-PIN DFA live states:", v.weak_pin_dfa().size()[1])
    print("Password: 5 component DFAs, states side by side:", 2 * 4 + 17)
    print("Password product (reachable, incl. trap):", v.password_product().size()[0])
    print("Password minimal (incl. trap):", v.password_minimal().size()[0])
    print("E-mail NFA states:", len(v.email_nfa().states()))
    print("E-mail subset DFA live states:", v.email_subset_dfa().size()[1])
    print("E-mail minimal DFA live states:", v.email_minimal().size()[1])


def main(argv):
    if argv == ["table"]:
        return table()
    if argv == ["sizes"]:
        return sizes()
    if len(argv) == 2 and argv[0] in APPS:
        return show(*argv)
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
