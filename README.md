# FLA Coursework - Formal Language and Automata

**Repository:** `FLA_TASK_KARTHIKEYA_-RA2411026050030-`  
**Course:** 21CSC301T Formal Language and Automata (CLA-2)  

---

## Overview

This repository contains implementations and verification suites for Formal Language and Automata coursework:

1. **Finite-Automata-Validators (Task 2)**
   - Real-time input validators modelled using Finite Automata (DFA, NFA, product automata, minimization).
   - Validates ATM PIN (length & weak patterns), card lock state machine, strong password policies, and email formatting.
   - Includes full unit test suite and a self-contained interactive browser demo.

2. **PDA-CFG-Case-Studies (Task 3)**
   - Pushdown Automata (PDA) simulator over instantaneous descriptions and Context-Free Grammar (CFG) analysis toolkit.
   - Case studies: balanced bracket sequences, arithmetic expression evaluation with ambiguity resolution & LL(1) parsing, and palindrome language recognition.
   - Comprehensive unit test verification.

---

## Directory Structure

```
FLA_/
├── .gitignore
├── README.md
├── Finite-Automata-Validators/
│   ├── fa_validators/
│   │   ├── automata.py
│   │   ├── validators.py
│   │   └── cli.py
│   ├── tests/
│   │   └── test_validators.py
│   ├── web/
│   │   ├── template.html
│   │   └── index.html
│   ├── build_web.py
│   └── README.md
└── PDA-CFG-Case-Studies/
    ├── pda_cfg/
    │   ├── pda.py
    │   ├── cfg.py
    │   ├── cases.py
    │   └── cli.py
    ├── tests/
    │   └── test_pda_cfg.py
    └── README.md
```
