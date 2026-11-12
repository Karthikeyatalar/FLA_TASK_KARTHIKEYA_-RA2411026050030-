"""Context-free grammars: parsing text, parse-tree counting, string generation,
CFG -> PDA, and an LL(1) table-driven parser."""
from functools import lru_cache
from .pda import PDA

EPS = "eps"


class CFG:
    def __init__(self, name, text, start=None):
        self.name, self.prods, order = name, {}, []
        for line in text.strip().splitlines():
            lhs, rhs = line.split("->")
            lhs = lhs.strip()
            order.append(lhs)
            for alt in rhs.split("|"):
                syms = tuple(alt.split())
                self.prods.setdefault(lhs, []).append(() if syms in [(EPS,), ("ε",)] else syms)
        self.start = start or order[0]
        self.nonterminals = set(self.prods)
        self.terminals = {s for ps in self.prods.values() for p in ps for s in p if s not in self.nonterminals}
        self._minlen = self._min_lengths()

    def _min_lengths(self):
        m = {A: 10 ** 9 for A in self.prods}
        changed = True
        while changed:
            changed = False
            for A, ps in self.prods.items():
                for p in ps:
                    n = sum(m[s] if s in m else 1 for s in p)
                    if n < m[A]:
                        m[A], changed = n, True
        return m

    def nullable(self):
        return {A for A, n in self._minlen.items() if n == 0}

    # -- number of distinct parse trees of a token sequence (>1 means the grammar is ambiguous there)
    def count_trees(self, tokens):
        w = tuple(tokens)
        mn = lambda x: self._minlen.get(x, 1)

        @lru_cache(maxsize=None)
        def sym(s, i, j):
            if s not in self.prods:
                return 1 if j - i == 1 and w[i] == s else 0
            if j - i < self._minlen[s]:
                return 0
            return sum(seq(p, i, j) for p in self.prods[s])

        @lru_cache(maxsize=None)
        def seq(p, i, j):
            if not p:
                return 1 if i == j else 0
            if len(p) == 1:
                return sym(p[0], i, j)
            rest = sum(mn(x) for x in p[1:])
            return sum(sym(p[0], i, k) * seq(p[1:], k, j)
                       for k in range(i + mn(p[0]), j - rest + 1))

        return sym(self.start, 0, len(w))

    def generates(self, tokens):
        return self.count_trees(tokens) > 0

    def generate(self, max_len):
        """All terminal strings (as tuples) of length <= max_len, by pruned leftmost expansion."""
        def lo(form):
            return sum(self._minlen.get(s, 1) for s in form)
        out, seen, todo = set(), {(self.start,)}, [(self.start,)]
        while todo:
            form = todo.pop()
            k = next((i for i, s in enumerate(form) if s in self.prods), None)
            if k is None:
                out.add(form)
                continue
            for p in self.prods[form[k]]:
                nf = form[:k] + p + form[k + 1:]
                if lo(nf) <= max_len and nf not in seen:
                    seen.add(nf)
                    todo.append(nf)
        return sorted(out, key=lambda t: (len(t), t))

    def leftmost_derivations(self, tokens, limit=10):
        """All leftmost derivations of the token sequence (as lists of sentential forms)."""
        w, res = tuple(tokens), []

        def go(form, hist):
            if len(res) >= limit:
                return
            k = next((i for i, s in enumerate(form) if s in self.prods), None)
            pre = form[:k] if k is not None else form
            if pre != w[:len(pre)] or len(pre) > len(w):
                return
            if k is None:
                if form == w:
                    res.append(hist)
                return
            for p in self.prods[form[k]]:
                nf = form[:k] + p + form[k + 1:]
                if sum(self._minlen.get(s, 1) for s in nf) <= len(w):
                    go(nf, hist + [nf])

        go((self.start,), [(self.start,)])
        return res

    def to_pda(self):
        """Standard construction: one state, accept by empty stack, one move per rule."""
        d = {}
        for A, ps in self.prods.items():
            d[("q", "", A)] = {("q", p) for p in ps}
        for a in self.terminals:
            d[("q", a, a)] = {("q", ())}
        bound = (lambda rest: rest) if not self.nullable() else None   # prune runaway left recursion
        return PDA(self.name + " -> PDA", d, "q", self.start, accept_by="empty", stack_bound=bound)

    def choice_points(self):
        return sorted(A for A, ps in self.prods.items() if len(ps) > 1)

    # -- LL(1)
    def first_follow(self):
        first = {A: set() for A in self.prods}
        nul = self.nullable()
        def first_seq(p):
            out = set()
            for s in p:
                if s in self.prods:
                    out |= first[s] - {EPS}
                    if s not in nul:
                        return out
                else:
                    return out | {s}
            return out | {EPS}
        changed = True
        while changed:
            changed = False
            for A, ps in self.prods.items():
                for p in ps:
                    f = first_seq(p)
                    if not f <= first[A]:
                        first[A] |= f
                        changed = True
        follow = {A: set() for A in self.prods}
        follow[self.start].add("$")
        changed = True
        while changed:
            changed = False
            for A, ps in self.prods.items():
                for p in ps:
                    for i, s in enumerate(p):
                        if s in self.prods:
                            f = first_seq(p[i + 1:])
                            new = (f - {EPS}) | (follow[A] if EPS in f else set())
                            if not new <= follow[s]:
                                follow[s] |= new
                                changed = True
        return first, follow, first_seq

    def ll1_table(self):
        """Return (table, conflicts). A non-empty conflict list means the grammar is not LL(1)."""
        first, follow, first_seq = self.first_follow()
        table, conflicts = {}, []
        for A, ps in self.prods.items():
            for p in ps:
                f = first_seq(p)
                for a in (f - {EPS}) | (follow[A] if EPS in f else set()):
                    if (A, a) in table and table[(A, a)] != p:
                        conflicts.append((A, a))
                    table[(A, a)] = p
        return table, conflicts

    def ll1_parse(self, tokens):
        table, conflicts = self.ll1_table()
        if conflicts:
            raise ValueError(f"not LL(1): {conflicts}")
        stack, toks, i = ["$", self.start], list(tokens) + ["$"], 0
        while stack:
            top = stack.pop()
            if top in self.prods:
                p = table.get((top, toks[i]))
                if p is None:
                    return False
                stack.extend(reversed(p))
            else:
                if top != toks[i]:
                    return False
                i += 1
        return i == len(toks)
