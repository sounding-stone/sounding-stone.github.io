#!/usr/bin/env python3
"""suite_cap.py LOG -- why did this Playwright run fail?

Reads a Playwright list/line-reporter log (raw, or with GitHub Actions
"job<TAB>step<TAB>timestamp " prefixes) and answers from the summary
block, never from the first red mark.

  exit 0  PASS            every planned test passed
  exit 1  TEST_FAILURE    summary reports failed tests, no suite cap
  exit 2  SUITE_TIMEOUT   the suite-level clock ran out (globalTimeout);
                          any failed tests are reported alongside
  exit 3  NO_SUMMARY      no summary block found: refuse to guess

Needs Python 3.8+ (no third-party packages).
"""
import re, sys

PREFIX = r"^(?:[^\t]*\t[^\t]*\t\S+Z )?"          # optional GitHub Actions prefix
COUNT = re.compile(PREFIX + r"\s*(\d+) (passed|failed|flaky|skipped|did not run|interrupted)"
                   r"(?: \(([\d.]+)(ms|s|m|h)\))?\s*$")
PLANNED = re.compile(PREFIX + r"Running (\d+) tests? using")
CAP = re.compile(PREFIX + r"Timed out waiting (\d+)s for the test suite to run\s*$")

def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return [re.sub(r"\x1b\[[0-9;]*m", "", l.rstrip("\n")) for l in f]

def main(path):
    lines = read(path)
    counts, planned, cap_s, wall = {}, None, None, None
    for l in lines:
        if m := PLANNED.match(l): planned = int(m.group(1))
        if m := CAP.match(l): cap_s = int(m.group(1))
        if m := COUNT.match(l):
            counts[m.group(2)] = int(m.group(1))
            if m.group(3): wall = m.group(3) + m.group(4)
    if not counts:
        print("verdict: NO_SUMMARY (no 'N passed' / 'N failed' line found)")
        return 3
    seen = sum(counts.values())
    print(f"planned: {planned}  " + "  ".join(f"{k}: {v}" for k, v in counts.items())
          + f"  wall: {wall}")
    if planned is not None and seen != planned:
        print(f"unaccounted: {planned - seen} (planned {planned}, summary lines add up to {seen})")
    failed = counts.get("failed", 0)
    if cap_s is not None:
        extra = f" + {failed} failed test(s)" if failed else ""
        print(f"verdict: SUITE_TIMEOUT (suite clock {cap_s}s ran out{extra}; "
              f"{counts.get('did not run', 0)} did not run)")
        return 2
    if failed:
        print(f"verdict: TEST_FAILURE ({failed} failed)")
        return 1
    print("verdict: PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
