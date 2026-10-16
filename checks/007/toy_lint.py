#!/usr/bin/env python3
"""Toy lint with one layer, P: a todo line marked (tentative) must not contain a prep word.
The config loader has the same shape as the real one: a single-line regex."""
import re, sys
from pathlib import Path

MARK = "(tentative)"
TERMS_LINE = re.compile(r"^\s*prep_terms:\s*\[(.*)\]\s*$")
ITEM = re.compile(r"'((?:[^']|'')*)'")

def load_terms(path):
    p = Path(path)
    if not p.exists():
        return None, f"P SKIP (cannot read {p.name})"
    for line in p.read_text(encoding="utf-8").splitlines():
        m = TERMS_LINE.match(line)
        if m:
            terms = [t for t in ITEM.findall(m.group(1)) if t]
            return [re.compile(t) for t in terms], f"P on: {len(terms)} terms"
    return None, f"P SKIP ({p.name} has no prep_terms)"

def main(todo, config):
    terms, note = load_terms(config)
    hits = []
    for no, line in enumerate(Path(todo).read_text(encoding="utf-8").splitlines(), 1):
        if MARK in line and terms:
            t = next((t.pattern for t in terms if t.search(line)), None)
            if t:
                hits.append(f"   [P-prep] line {no}: prep word '{t}' on a tentative line")
    if hits:
        print(f"lint: FAIL - {len(hits)} line(s) · {note}")
        print("\n".join(hits))
        return 1
    print(f"lint: OK · {note}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
