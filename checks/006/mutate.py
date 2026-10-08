#!/usr/bin/env python3
"""mutate.py -- break alias_check.py on purpose; every mutant should make controls.py fail."""
import subprocess, sys
tool = sys.argv[1] if len(sys.argv) > 1 else "../alias_check.py"; src = open(tool).read()
M = [
 ("case spelling not tried",       '    variants = {"case": Path(str(p).replace("Café/Tasks/Main.md", "cAFÉ/tASKS/mAIN.MD")),\n                "unicode', '    variants = {"unicode'),
 ("NFD spelling not tried",        ',\n                "unicode (NFD)": Path(str(p).replace("Café", unicodedata.normalize("NFD", "Café")))}', '}'),
 ("hard link not tried",           'os.link(p, base / "hard.md"); same["hard link"] = base / "hard.md"', 'pass'),
 ("no distinct files",             '    return p, same, other', '    return p, same, {}'),
 ("byte-identical copy not tried", 'other["byte-identical copy"] = base / "copy.md"', 'pass'),
 ("guard crash counted as right",  'except Exception as e: got = f"{type(e).__name__}"', 'except Exception as e: got = want'),
 ("truthy string accepted",        'ok = got is want', 'ok = bool(got) == want'),
 ("only first 3 cases (head)",     'for name, c in group.items():', 'for name, c in list(group.items())[:3]:'),
 ("wrong answers exit 0",          'return 1 if wrong else 0', 'return 0'),
 ("usage error exits 0",           'print("usage: alias_check.py FILE.py:FUNCTION"); return 2', 'print("usage: alias_check.py FILE.py:FUNCTION"); return 0'),
 ("spelling kept without opening it", 'if v.exists(): same[name] = v', 'if True: same[name] = v'),
]
survived = 0
for name, a, b in M:
    assert src.count(a) == 1, f"anchor not unique: {name}"
    open("_mutant.py", "w").write(src.replace(a, b))
    rc = subprocess.run([sys.executable, "controls.py", "_mutant.py"], capture_output=True, text=True).returncode
    survived += rc == 0
    print(f"{'caught  ' if rc else 'SURVIVED'} ({rc} controls failed)  {name}")
print(f"{len(M)} mutants, {len(M) - survived} caught, {survived} survived")
