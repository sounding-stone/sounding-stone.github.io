#!/usr/bin/env python3
"""controls.py [CHECKER] -- run alias_check.py against predicates whose right answers are known.
Expected MISS sets are for a default (case-insensitive) APFS volume."""
import re, subprocess, sys
tool = sys.argv[1] if len(sys.argv) > 1 else "../alias_check.py"
ALL_SAME = {"symlink", "symlinked parent", "dot-dot", "hard link", "case", "unicode (NFD)"}
WANT = {  # predicate: (exit code, names that must be MISS)
    "resolve_eq":  (1, {"hard link", "case", "unicode (NFD)"}),   # known positive: the fence as first written
    "casefold_eq": (1, {"hard link", "unicode (NFD)"}),
    "string_eq":   (1, ALL_SAME),
    "samefile":    (0, set()),
    "bytes_eq":    (1, {"byte-identical copy"}),
    "always":      (1, {"sibling", "byte-identical copy"}),
    "raises":      (1, ALL_SAME | {"exact", "sibling", "byte-identical copy"}),
}
bad = 0
for g, (rc, miss) in WANT.items():
    p = subprocess.run([sys.executable, tool, f"guards.py:{g}"], capture_output=True, text=True)
    got = {m.strip() for m in re.findall(r"^MISS  (.+?) +->", p.stdout, re.M)}
    ok = p.returncode == rc and got == miss
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {g:12} rc={p.returncode} (want {rc})" + ("" if ok else f"  MISS={sorted(got)} want {sorted(miss)}"))
p = subprocess.run([sys.executable, tool], capture_output=True, text=True)
ok = p.returncode == 2; bad += not ok
print(f"{'ok  ' if ok else 'FAIL'} {'(no args)':12} rc={p.returncode} (want 2)")
sys.exit(bad)
