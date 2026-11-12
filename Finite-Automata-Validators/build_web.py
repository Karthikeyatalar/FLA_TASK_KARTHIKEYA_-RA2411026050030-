"""Generate web/index.html: a self-contained page that runs the same DFAs in the browser.
   python build_web.py"""
import json
from fa_validators import validators as v

def export(dfa, cls):
    table = {}
    for (q, a), r in dfa.delta.items():
        table.setdefault(q, {})[a] = r
    return {"name": dfa.name, "start": dfa.start, "accepts": sorted(dfa.accepts), "trap": dfa.trap,
            "delta": table, "classifier": cls}

DATA = {
    "pin": export(v.pin_dfa(), "pin"),
    "card": export(v.card_lock_dfa(), "none"),
    "password": export(v.password_minimal(), "password"),
    "email": export(v.email_minimal(), "email"),
}
LABELS = {"pin": "ATM PIN (4 digits)", "card": "Card lock (events C/W)",
          "password": "Password policy", "email": "E-mail format"}
TEMPLATE = open("web/template.html", encoding="utf-8").read()
html = TEMPLATE.replace("__DATA__", json.dumps(DATA)).replace("__LABELS__", json.dumps(LABELS))
open("web/index.html", "w", encoding="utf-8").write(html)
print("wrote web/index.html")
