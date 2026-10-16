#!/usr/bin/env python3
"""Known answers for skip_canary.py. Usage: python3 controls.py [canary.py]"""
import subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANARY = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "skip_canary.py"
GOOD = "rules:\n  prep_terms: ['before', 'prepare', 'Read']\n"
CONFIGS = {
    "good config":            GOOD,
    "trailing comment":       "rules:\n  prep_terms: ['before', 'prepare', 'Read']  # added Read\n",
    "unquoted list (valid YAML)": "rules:\n  prep_terms: [before, prepare, Read]\n",
    "block list (valid YAML)":    "rules:\n  prep_terms:\n    - before\n    - prepare\n",
    "key typo":               "rules:\n  prep_term: ['before', 'prepare']\n",
}
LINTS = {
    "always red":  "import sys; print('lint: FAIL\\n   [P-prep] line 1'); sys.exit(1)",
    "warn only":   "import sys; print('lint: WARN\\n   [P-prep] line 1'); sys.exit(0)",
    "finds then errors": "import sys; from pathlib import Path\n"
                   "bad = 'prepare' in Path(sys.argv[1]).read_text()\n"
                   "print('   [P-prep] line 1\\nOSError: cannot write' if bad else 'lint: OK'); sys.exit(2 if bad else 0)",
    "crashes":     "import sys; print('Traceback ...'); sys.exit(2)",
    "wrong layer": "import sys; from pathlib import Path\n"
                   "bad = 'prepare' in Path(sys.argv[1]).read_text()\n"
                   "print('lint: FAIL\\n   [K-keyword] line 1' if bad else 'lint: OK'); sys.exit(1 if bad else 0)",
}
CASES = [(name, "toy", name, "REJECT" if name != "good config" else "ACCEPT") for name in CONFIGS]
CASES += [("config file missing", "toy", None, "REJECT")]
CASES += [(name, name, "good config", "REJECT") for name in LINTS]

def main():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "pos.md").write_text("- [ ] Planning sync, tentative; prepare slides first (tentative)\n")
        (d / "neg.md").write_text("- [ ] Planning sync: undecided, accept or decline (tentative)\n")
        for name, text in CONFIGS.items():
            (d / (name.split(" (")[0].replace(" ", "_") + ".yaml")).write_text(text)
        for name, src in LINTS.items():
            (d / (name.replace(" ", "_") + ".py")).write_text(src)
        ok = 0
        for case, lint, cfg, want in CASES:
            script = HERE / "toy_lint.py" if lint == "toy" else d / (lint.replace(" ", "_") + ".py")
            cfgpath = d / ((cfg or "missing").split(" (")[0].replace(" ", "_") + ".yaml")
            r = subprocess.run([sys.executable, str(CANARY), "--cmd", f"{sys.executable} {script} {{input}} {{config}}",
                                "--config", str(cfgpath), "--positive", str(d / "pos.md"),
                                "--negative", str(d / "neg.md"), "--expect", "[P-prep]"],
                               capture_output=True, text=True)
            got = "ACCEPT" if r.returncode == 0 else "REJECT"
            ok += got == want
            print(f"{'ok ' if got == want else 'BAD'} {case:28} want {want:6} got {got}")
        print(f"{ok}/{len(CASES)} controls")
        return 0 if ok == len(CASES) else 1

if __name__ == "__main__":
    sys.exit(main())
