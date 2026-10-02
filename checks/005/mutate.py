#!/usr/bin/env python3
"""mutate.py -- break suite_cap.py on purpose; every mutant must make controls.py fail."""
import subprocess, sys
import sys
tool = sys.argv[1] if len(sys.argv) > 1 else "../suite_cap.py"
src = open(tool).read()
M = [
 ("count regex unanchored (search, no $)", 'if m := COUNT.match(l):', 'if m := re.search(r"(\\d+) (passed|failed|flaky|skipped|did not run|interrupted)(?: \\(([\\d.]+)(ms|s|m|h)\\))?", l):'),
 ("suite-timeout line ignored",            'if m := CAP.match(l): cap_s = int(m.group(1))', 'pass'),
 ("verdict taken from first red mark",     '    lines = read(path)\n', '    lines = read(path)\n    if any("\\u2718" in l for l in lines):\n        print("verdict: TEST_FAILURE"); return 1\n'),
 ("read from the red mark downward",       '    lines = read(path)\n', '    lines = read(path)\n    i = next((k for k, l in enumerate(lines) if "\\u2718" in l), 0); lines = lines[i:]\n'),
 ("only the first 30 lines (head -30)",    '    lines = read(path)\n', '    lines = read(path)[:30]\n'),
 ("TEST_FAILURE exits 0",                  '        return 1\n    print("verdict: PASS")', '        return 0\n    print("verdict: PASS")'),
 ("NO_SUMMARY exits 0 (guesses PASS)",     '        return 3', '        return 0'),
 ("no CI prefix support",                  'PREFIX = r"^(?:[^\\t]*\\t[^\\t]*\\t\\S+Z )?"', 'PREFIX = r"^"'),
 ("'did not run' not counted",             '|did not run|interrupted)"', '|interrupted)"'),
 ("cap regex keyed on teardown line",      'for the test suite to run', 'for the teardown for test suite to run'),
]
survived = 0
for name, a, b in M:
    assert src.count(a) == 1, f"anchor not unique: {name}"
    open("_mutant.py", "w").write(src.replace(a, b))
    rc = subprocess.run([sys.executable, "controls.py", "_mutant.py"], capture_output=True, text=True).returncode
    caught = rc != 0
    survived += not caught
    print(f"{'caught  ' if caught else 'SURVIVED'} ({rc} controls failed)  {name}")
print(f"{len(M)} mutants, {len(M) - survived} caught, {survived} survived")
