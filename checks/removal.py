#!/usr/bin/env python3
"""removal.py BEFORE AFTER ID - did removing entry ID change anything else?

Checks the result of deleting one entry from a YAML list of mappings
(default: top-level key 'watches', entries identified by 'id').

  REMOVED      after == before minus exactly that entry           exit 0
  DAMAGED      parses, but something other than that entry moved  exit 1
  UNPARSEABLE  a strict parse fails (duplicate keys are fatal)    exit 1

Built-in controls run first on every invocation. If they do not come out
as expected, nothing is classified and the exit status is 2. An unreadable
input file exits 3.
Needs PyYAML (pip install pyyaml).
"""
import sys, yaml

class Strict(yaml.SafeLoader):
    pass

def _mapping(loader, node, deep=False):
    seen = {}
    for k, _ in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in seen:
            raise yaml.YAMLError(f"duplicate key {key!r} at lines {seen[key]} and {k.start_mark.line + 1}")
        seen[key] = k.start_mark.line + 1
    return yaml.SafeLoader.construct_mapping(loader, node, deep)

Strict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)

def classify(before_txt, after_txt, wid, list_key="watches", id_key="id"):
    try:
        b = yaml.load(before_txt, Loader=Strict)
        a = yaml.load(after_txt, Loader=Strict)
    except yaml.YAMLError as e:
        return "UNPARSEABLE", str(e).splitlines()[0]
    if not (isinstance(b, dict) and isinstance(a, dict)):
        return "UNPARSEABLE", "top level is not a mapping"
    bl, al = b.get(list_key), a.get(list_key)
    if not (isinstance(bl, list) and isinstance(al, list)):
        return "UNPARSEABLE", f"{list_key!r} is not a list in both files"
    targets = [e for e in bl if isinstance(e, dict) and e.get(id_key) == wid]
    if len(targets) != 1:
        return "DAMAGED", f"{len(targets)} entries with {id_key}={wid!r} in BEFORE, expected 1"
    expected = [e for e in bl if e is not targets[0]]
    problems = []
    if {k: v for k, v in b.items() if k != list_key} != {k: v for k, v in a.items() if k != list_key}:
        problems.append("top-level keys outside the list changed")
    if len(al) != len(expected):
        problems.append(f"{len(al)} entries after, expected {len(expected)}")
    for old, new in zip(expected, al):
        if old == new:
            continue
        name = old.get(id_key) if isinstance(old, dict) else repr(old)
        if not (isinstance(old, dict) and isinstance(new, dict)):
            problems.append(f"{name}: entry replaced")
            continue
        for k in sorted(set(old) | set(new), key=str):
            if k not in new:
                problems.append(f"{name}: lost {k!r}")
            elif k not in old:
                problems.append(f"{name}: gained {k!r}")
            elif old[k] != new[k]:
                problems.append(f"{name}: {k!r} changed")
    return ("DAMAGED", "; ".join(problems)) if problems else ("REMOVED", "")

HEAD = "watches:\n  - id: a\n    expiry: '2026-10-31'\n    note: first\n\n"
TAIL = "  - id: c\n    expiry: '2026-11-30'\n"
CONTROLS = [  # (expected verdict, label, before, after, id)
    ("UNPARSEABLE", "orphaned tail, keys shared with neighbour",
     HEAD + "  - id: b\n    expiry: '2026-10-31'\n\n    note: second\n\n" + TAIL,
     HEAD + "    note: second\n\n" + TAIL, "b"),
    ("DAMAGED", "orphaned tail, key new to neighbour",
     HEAD + "  - id: b\n    expiry: '2026-10-31'\n\n    probe: x\n\n" + TAIL,
     HEAD + "    probe: x\n\n" + TAIL, "b"),
    ("UNPARSEABLE", "BEFORE already had a duplicate key",
     "watches:\n  - id: a\n    note: one\n    note: two\n  - id: b\n    note: x\n",
     "watches:\n  - id: a\n    note: one\n    note: two\n", "b"),
    ("DAMAGED", "a top-level key outside the list went missing",
     HEAD + "  - id: b\n    note: x\nchannels: [general]\n",
     HEAD.rstrip("\n") + "\n", "b"),
    ("REMOVED", "clean removal",
     HEAD + "  - id: b\n    expiry: '2026-10-31'\n\n    note: second\n\n" + TAIL,
     HEAD + TAIL, "b"),
]

def main(argv):
    if len(argv) != 4:
        print(__doc__.strip()); return 64
    ok = True
    for want, label, bt, at, wid in CONTROLS:
        got, why = classify(bt, at, wid)
        sign = "-" if want == "REMOVED" else "+"
        print(f"control {sign}  {got:<12} {label}" + ("" if got == want else f"   <- expected {want}"))
        ok &= got == want
    if not ok:
        print("controls did not separate; refusing to classify."); return 2
    try:
        before, after, wid = open(argv[1]).read(), open(argv[2]).read(), argv[3]
    except OSError as e:
        print(f"cannot read input: {e}"); return 3
    got, why = classify(before, after, wid)
    print(f"\n{got:<12} {argv[2]}  (removed {wid!r} from {argv[1]})" + (f"\n             {why}" if why else ""))
    return 0 if got == "REMOVED" else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
