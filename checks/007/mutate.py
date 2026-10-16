#!/usr/bin/env python3
"""Break skip_canary.py on purpose; each break must make controls.py fail."""
import subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE.parent / "skip_canary.py").read_text()
MUTANTS = {
    "no positive check":      ('    if rc != 1:\n', '    if False:\n'),
    "any non-zero = fired":   ('    if rc != 1:\n', '    if rc == 0:\n'),
    "no layer tag check":     ('    elif a.expect not in out:\n', '    elif False:\n'),
    "no negative check":      ('    if rc != 0:\n', '    if False:\n'),
    "trust the exit code of the run, ignore problems": ('    return 1 if problems else 0\n', '    return 0\n'),
    "test a copy, not the live config": ('    rc, out = run(a.cmd, a.positive, a.config)\n',
        '    import tempfile, os; c = tempfile.mktemp(suffix=".yaml"); open(c, "w").write("rules:\\n  prep_terms: [\'prepare\']\\n"); a.config = c\n'
        '    rc, out = run(a.cmd, a.positive, a.config)\n'),
}

def main():
    killed = 0
    for name, (old, new) in MUTANTS.items():
        assert SRC.count(old) == 1, name
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "skip_canary.py"
            m.write_text(SRC.replace(old, new))
            r = subprocess.run([sys.executable, str(HERE / "controls.py"), str(m)], capture_output=True, text=True)
            bad = [l.split(" want")[0][4:].strip() for l in r.stdout.splitlines() if l.startswith("BAD")]
            killed += r.returncode != 0
            print(f"{'killed  ' if r.returncode else 'SURVIVED'} {name:50} {', '.join(bad)}")
    print(f"{killed}/{len(MUTANTS)} mutants killed")

if __name__ == "__main__":
    main()
