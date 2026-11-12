# FLA Task 2 - Finite Automata for Real-Time Validation

21CSC301T Formal Language and Automata, CLA-2 (individual work)
K. R. Vaishak (RA2411026050018), SRM Institute of Science and Technology, Tiruchirappalli

Three input checks modelled as finite automata, built with a small library
(DFA, NFA, subset construction, product, minimisation). Standard library only, Python 3.9+.

| Application | Automaton | Live states |
|---|---|---|
| ATM PIN (4 digits) | DFA over {D, O} | 5 |
| PIN, not all digits equal | DFA over 0-9 | 34 |
| Card lock (3 wrong PINs) | DFA over {C, W} | 5 |
| Password 8-16 chars, U/L/D/S | 5 component DFAs (25 states) -> product -> minimal | 224 -> 196 |
| E-mail format | NFA (9) -> subset DFA (9) -> minimal DFA | 8 |

## Run
    python -m fa_validators.cli email vaishak@srm.c0m   # step-by-step trace
    python -m fa_validators.cli table                    # accept/reject tables
    python -m fa_validators.cli sizes                    # state counts
    python -m unittest discover -s tests -v              # 21 tests
    python build_web.py                                  # regenerate web/index.html (open in a browser)

## Layout
    fa_validators/automata.py    DFA, NFA, subset_construction, product, minimise
    fa_validators/validators.py  PIN, card lock, password, e-mail automata and classifiers
    fa_validators/cli.py         command-line demo
    tests/test_validators.py     every automaton vs an independent Python rule
    web/                         live browser demo (template.html + generated index.html)
