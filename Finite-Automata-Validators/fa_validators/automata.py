"""Small finite-automata library: DFA, NFA, subset construction, product, minimisation.

Every DFA is complete. Transitions into the trap state are not stored; a missing entry
means "go to the trap" (default name 'qD'), so diagrams can omit the trap.
"""
from collections import deque


class DFA:
    def __init__(self, name, alphabet, delta, start, accepts, trap="qD"):
        self.name, self.alphabet = name, tuple(alphabet)
        self.delta, self.start = dict(delta), start
        self.accepts, self.trap = set(accepts), trap

    def step(self, q, sym):
        return self.delta.get((q, sym), self.trap)

    def run(self, symbols):
        q = self.start
        for s in symbols:
            q = self.step(q, s)
        return q

    def accepts_symbols(self, symbols):
        return self.run(symbols) in self.accepts

    def trace(self, symbols, chars=None):
        """Return [(i, state, char, symbol, next_state)] and the final state."""
        rows, q = [], self.start
        for i, s in enumerate(symbols):
            r = self.step(q, s)
            rows.append((i + 1, q, chars[i] if chars else s, s, r))
            q = r
        return rows, q

    def reachable(self):
        seen, todo = {self.start}, deque([self.start])
        while todo:
            q = todo.popleft()
            for a in self.alphabet:
                r = self.step(q, a)
                if r not in seen:
                    seen.add(r)
                    todo.append(r)
        return seen

    def live_states(self):
        """Reachable states from which an accepting state can still be reached."""
        reach = self.reachable()
        back = {q: set() for q in reach}
        for q in reach:
            for a in self.alphabet:
                back[self.step(q, a)].add(q)
        live, todo = set(self.accepts & reach), deque(self.accepts & reach)
        while todo:
            for p in back[todo.popleft()]:
                if p not in live:
                    live.add(p)
                    todo.append(p)
        return live

    def size(self):
        """(total reachable states incl. trap, live states without trap)"""
        return len(self.reachable()), len(self.live_states())


class NFA:
    """NFA without epsilon moves. delta maps (state, symbol) -> set of states."""

    def __init__(self, name, alphabet, delta, start, accepts):
        self.name, self.alphabet = name, tuple(alphabet)
        self.delta, self.start, self.accepts = delta, start, set(accepts)

    def states(self):
        s = {self.start} | self.accepts
        for (q, _), rs in self.delta.items():
            s.add(q)
            s |= set(rs)
        return s

    def accepts_symbols(self, symbols):
        cur = {self.start}
        for s in symbols:
            cur = set().union(*[self.delta.get((q, s), set()) for q in cur]) if cur else set()
        return bool(cur & self.accepts)


def subset_construction(nfa):
    """NFA -> DFA. The empty set becomes the trap state qD. States are frozensets."""
    start = frozenset({nfa.start})
    delta, seen, todo = {}, {start}, deque([start])
    while todo:
        S = todo.popleft()
        for a in nfa.alphabet:
            T = frozenset(set().union(*[nfa.delta.get((q, a), set()) for q in S]))
            if not T:
                continue
            delta[(S, a)] = T
            if T not in seen:
                seen.add(T)
                todo.append(T)
    acc = {S for S in seen if S & nfa.accepts}
    return DFA(nfa.name + " (subset DFA)", nfa.alphabet, delta, start, acc)


def product(dfas, name="product"):
    """Intersection of DFAs over one alphabet; reachable part only.
    A tuple in which any component is in its own trap collapses to the single trap qD."""
    alpha = dfas[0].alphabet
    trap = "qD"

    def norm(t):
        return trap if any(q == d.trap for q, d in zip(t, dfas)) else t

    start = norm(tuple(d.start for d in dfas))
    delta, seen, todo = {}, {start}, deque([start])
    while todo:
        t = todo.popleft()
        if t == trap:
            continue
        for a in alpha:
            r = norm(tuple(d.step(q, a) for q, d in zip(t, dfas)))
            if r != trap:
                delta[(t, a)] = r
            if r not in seen:
                seen.add(r)
                todo.append(r)
    acc = {t for t in seen if t != trap and all(q in d.accepts for q, d in zip(t, dfas))}
    return DFA(name, alpha, delta, start, acc, trap)


def minimise(dfa, prefix="m", name=None):
    """Moore partition refinement on the reachable part; states renamed in BFS order."""
    reach = sorted(dfa.reachable(), key=str)
    block = {q: (q in dfa.accepts) for q in reach}
    while True:
        sig = {q: (block[q],) + tuple(block[dfa.step(q, a)] for a in dfa.alphabet) for q in reach}
        ids = {}
        new = {q: ids.setdefault(sig[q], len(ids)) for q in reach}
        stable = len(set(new.values())) == len(set(block.values()))
        block = new
        if stable:
            break
    live = dfa.live_states()
    dead = [q for q in reach if q not in live]
    trap_block = block[dead[0]] if dead else None
    rep = {}
    for q in reach:
        rep.setdefault(block[q], q)
    names, order, seen, i = {}, deque([block[dfa.start]]), {block[dfa.start]}, 0
    while order:  # BFS naming
        b = order.popleft()
        if b == trap_block:
            names[b] = dfa.trap
        else:
            names[b] = f"{prefix}{i}"
            i += 1
        for a in dfa.alphabet:
            nb = block[dfa.step(rep[b], a)]
            if nb not in seen:
                seen.add(nb)
                order.append(nb)
    delta = {}
    for b in seen:
        if b == trap_block:
            continue
        for a in dfa.alphabet:
            nb = block[dfa.step(rep[b], a)]
            if nb != trap_block:
                delta[(names[b], a)] = names[nb]
    acc = {names[b] for b in seen if rep[b] in dfa.accepts}
    return DFA(name or dfa.name + " (minimal)", dfa.alphabet, delta, names[block[dfa.start]], acc, dfa.trap)
