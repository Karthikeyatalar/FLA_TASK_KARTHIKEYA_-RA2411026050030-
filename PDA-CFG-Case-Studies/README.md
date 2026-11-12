# FLA Task 3 - Case Studies with PDA and CFG

21CSC301T Formal Language and Automata, CLA-2 (individual work)
K. R. Vaishak (RA2411026050018), SRM Institute of Science and Technology, Tiruchirappalli

A PDA simulator over instantaneous descriptions, a CFG toolkit (parse-tree counting, string
generation, CFG -> PDA, LL(1) table and parser), and three case studies:
balanced brackets, arithmetic expressions, palindromes. Standard library only, Python 3.9+.

## Run
    python -m pda_cfg.cli ambiguity              # bounded ambiguity check
    python -m pda_cfg.cli expr                   # CFG / PDA / LL(1) agree; trees in ambiguous grammar
    python -m pda_cfg.cli brackets "if (a[i] > 0) { sum += f(a[i]); }"
    python -m pda_cfg.cli palindromes
    python -m unittest discover -s tests -v      # 17 tests

## Layout
    pda_cfg/pda.py     PDA (determinism check, BFS search, computation trace) + the 3 machines
    pda_cfg/cfg.py     CFG, count_trees, generate, to_pda, FIRST/FOLLOW, LL(1)
    pda_cfg/cases.py   grammars, bracket lexer, expression evaluator, random generators
    pda_cfg/cli.py     command-line tool
    tests/             machines vs independent checkers
