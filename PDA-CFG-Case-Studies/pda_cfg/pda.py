"""Pushdown automaton simulated over instantaneous descriptions (q, remaining input, stack).
The stack is a tuple with the TOP at index 0.  Transitions: (q, a, X) -> {(q2, push)} where
a == '' is an epsilon move and push is a tuple whose first symbol becomes the new top."""
from collections import deque


def T(x):
    return tuple(x) if not isinstance(x, tuple) else x


class PDA:
    def __init__(self, name, delta, start, z0, finals=(), accept_by="final", stack_bound=None):
        self.name, self.start, self.z0 = name, start, z0
        self.delta = {k: {(q, T(p)) for q, p in v} for k, v in delta.items()}
        self.finals, self.accept_by, self.stack_bound = set(finals), accept_by, stack_bound

    # -- determinism: no (q,X) with two options, and no epsilon move competing with an input move
    def determinism_conflicts(self):
        bad = []
        for (q, a, X), targets in self.delta.items():
            if len(targets) > 1:
                bad.append(f"two moves on ({q}, {a or 'eps'}, {X})")
            if a == "" and any(k[0] == q and k[2] == X and k[1] != "" for k in self.delta):
                bad.append(f"eps-move competes with input move in ({q}, {X})")
        return sorted(set(bad))

    def is_deterministic(self):
        return not self.determinism_conflicts()

    def _moves(self, cfg):
        q, rest, stack = cfg
        if not stack:
            return
        X, below = stack[0], stack[1:]
        for q2, push in self.delta.get((q, "", X), ()):
            yield (q2, rest, push + below)
        if rest:
            for q2, push in self.delta.get((q, rest[0], X), ()):
                yield (q2, rest[1:], push + below)

    def _accepting(self, cfg):
        q, rest, stack = cfg
        if rest:
            return False
        return (q in self.finals) if self.accept_by == "final" else (not stack)

    def search(self, word, max_configs=200000):
        """Breadth-first search. Returns (accepted, configs_explored, accepting_path or None)."""
        word = T(word)
        init = (self.start, word, (self.z0,) if self.z0 else ())
        parent, todo = {init: None}, deque([init])
        while todo:
            cfg = todo.popleft()
            if self._accepting(cfg):
                path = []
                while cfg is not None:
                    path.append(cfg)
                    cfg = parent[cfg]
                return True, len(parent), path[::-1]
            for nxt in self._moves(cfg):
                if self.stack_bound and len(nxt[2]) > self.stack_bound(len(nxt[1])):
                    continue
                if nxt not in parent and len(parent) < max_configs:
                    parent[nxt] = cfg
                    todo.append(nxt)
        return False, len(parent), None

    def accepts(self, word):
        return self.search(word)[0]

    def explain(self, word):
        """Return a list of ID strings: the accepting computation, or the run up to the dead end."""
        ok, n, path = self.search(word)
        fmt = lambda c: f"({c[0]},{''.join(c[1]) or 'eps'},{''.join(c[2]) or 'eps'})"
        if ok:
            return [fmt(c) for c in path], "accept"
        # follow the (unique, if deterministic) run as far as it goes
        cfg = (self.start, T(word), (self.z0,) if self.z0 else ())
        ids = [fmt(cfg)]
        while True:
            nxt = list(self._moves(cfg))
            if not nxt:
                break
            cfg = nxt[0]
            ids.append(fmt(cfg))
            if len(ids) > 200:
                break
        return ids, "reject"


# ---------- the three machines of the case studies ----------
OPEN = {"(": ")", "[": "]", "{": "}"}


def brackets_dpda():
    """3-state DPDA: push every opener, pop on the matching closer, eps to qf when Z0 is on top."""
    d = {}
    for o, c in OPEN.items():
        d[("q0", o, "Z")] = {("q1", o + "Z")}
        d[("qf", o, "Z")] = {("q1", o + "Z")}
        for X in OPEN:          # q1 reads no input with Z0 on top, so its eps-move never competes
            d[("q1", o, X)] = {("q1", o + X)}
        d[("q1", c, o)] = {("q1", "")}
    d[("q1", "", "Z")] = {("qf", "Z")}
    return PDA("Balanced brackets (DPDA)", d, "q0", "Z", {"qf"})


def wcwr_dpda():
    """w c w^R over {a,b}: push until c, then pop. Deterministic."""
    d = {}
    for a in "ab":
        d[("q0", a, "Z")] = {("q0", a + "Z")}
        for X in "ab":
            d[("q0", a, X)] = {("q0", a + X)}
        d[("q1", a, a)] = {("q1", "")}
    for X in ["Z", "a", "b"]:
        d[("q0", "c", X)] = {("q1", X)}
    d[("q1", "", "Z")] = {("q2", "Z")}
    return PDA("w c w^R (DPDA)", d, "q0", "Z", {"q2"})


def wwr_npda():
    """w w^R over {a,b}: the centre is guessed with an eps-move at every position."""
    d = {}
    for a in "ab":
        d[("q0", a, "Z")] = {("q0", a + "Z")}
        for X in "ab":
            d[("q0", a, X)] = {("q0", a + X)}
        d[("q1", a, a)] = {("q1", "")}
    for X in ["Z", "a", "b"]:
        d[("q0", "", X)] = {("q1", X)}
    d[("q1", "", "Z")] = {("q2", "Z")}
    return PDA("w w^R (NPDA)", d, "q0", "Z", {"q2"})
