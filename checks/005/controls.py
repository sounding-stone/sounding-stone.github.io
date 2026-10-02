#!/usr/bin/env python3
"""controls.py [path/to/suite_cap.py] -- run suite_cap against fixtures; exit = number of failed controls."""
import subprocess, sys
tool = sys.argv[1] if len(sys.argv) > 1 else "suite_cap.py"
CASES = [  # (fixture, expected exit, must contain, must not contain)
    ("cap",        2, ["SUITE_TIMEOUT", "3 did not run"], ["failed"]),
    ("cap_ci",     2, ["SUITE_TIMEOUT"], ["TEST_FAILURE"]),
    ("cap_ci_gh",  2, ["SUITE_TIMEOUT"], ["TEST_FAILURE"]),
    ("noisy_cap",  2, ["SUITE_TIMEOUT"], ["failed"]),
    ("fail",       1, ["TEST_FAILURE (1 failed)"], ["SUITE_TIMEOUT"]),
    ("failcap",    2, ["SUITE_TIMEOUT", "1 failed"], []),
    ("pass",       0, ["PASS"], ["failed"]),
    ("truncated",  3, ["NO_SUMMARY"], ["TEST_FAILURE"]),
]
bad = 0
for name, rc, must, mustnt in CASES:
    p = subprocess.run([sys.executable, tool, f"logs/{name}.log"], capture_output=True, text=True)
    out = p.stdout + p.stderr
    ok = p.returncode == rc and all(m in out for m in must) and not any(m in out for m in mustnt)
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name:10} rc={p.returncode} (want {rc})")
sys.exit(bad)
