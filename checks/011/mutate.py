#!/usr/bin/env python3
"""Break cleanup_check.py on purpose and see whether the target matrix notices."""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "cleanup_check.py")).read()
CNT_FIND = "find {root} -maxdepth 1 -name {pat} | wc -l"
CNT_LS = "ls -d {root}/{glob} 2>/dev/null | wc -l"
MATRIX = [  # (clean, count, expected exit)
    ("find {root} -maxdepth 1 -name {pat} -exec rmdir {} +", CNT_FIND, 1),
    ("find {root}/ -maxdepth 1 -name {pat} -delete", CNT_LS, 0),
    ("find {root}/ -maxdepth 1 -name {pat} | xargs rmdir", CNT_LS, 4),
    ("find {root}/ -mindepth 1 -maxdepth 1 -type d -exec rmdir {} +", CNT_LS, 4),
    ("find -H {root} -maxdepth 1 -name {pat} -delete", "find -H {root} -maxdepth 1 -name {pat} | wc -l", 0),
    ("find {root} -maxdepth 1 -name {pat} -exec rmdir {} +", CNT_LS, 4),
    ("find {root}/ -maxdepth 1 -name {pat} | xargs rmdir", "echo 0", 1),
    ("true", "echo removed 4, left 0", 1),
    ("find {root} -maxdepth 1 -name {pat} | xargs rmdir", CNT_FIND, 1),
]
MUTANTS = {
    "oracle looks with find, like the action": (
        "return [n for n in os.listdir(os.path.realpath(root)) if fnmatch.fnmatchcase(n, PAT)]",
        "return subprocess.run(['find', root, '-maxdepth', '1', '-name', PAT], capture_output=True, text=True).stdout.split(chr(10))[:-1] and [os.path.basename(x) for x in subprocess.run(['find', root, '-maxdepth', '1', '-name', PAT], capture_output=True, text=True).stdout.split(chr(10)) if x]"),
    "no symlink fixture": ('out = [("real directory", real), ("root is a symlink", link)]',
                           'out = [("real directory", real)]'),
    "no target name with a space": ('"proj-3", "proj-x y"]', '"proj-3", "proj-4"]'),
    "decoy check removed": ("if len(decoys) != len(DECOYS):", "if False:"),
    "false 0 needs left > 1": ("if said == 0 and left > 0:", "if said == 0 and left > 1:"),
    "count read from first integer": ("said, left = int(nums[-1])", "said, left = int(nums[0])"),
    "controls not enforced": ("    if bad:\n", "    if False:\n"),
    "fixture self-check removed": ("        if sorted(oracle(root)) != sorted(TARGETS):", "        if False:"),
    "fixture error exits 1": ("    sys.exit(3)\n\ndef oracle", "    sys.exit(1)\n\ndef oracle"),
    "pattern quoted for the shell too": ('.replace("{glob}", PAT)', '.replace("{glob}", shlex.quote(PAT))'),
    "worst() ranks NOT-CLEAN above FALSE-CLEAN": ('("FALSE-CLEAN", "NOT-CLEAN",', '("NOT-CLEAN", "FALSE-CLEAN",'),
}
def exits(src):
    with tempfile.TemporaryDirectory(dir=os.environ.get("CHECK_TMP")) as d:
        f = os.path.join(d, "m.py"); open(f, "w").write(src)
        return [subprocess.run([sys.executable, "-I", f, c, n], capture_output=True).returncode for c, n, _ in MATRIX]
want = [e for _, _, e in MATRIX]
base = exits(SRC)
print("unmutated:", base, "want", want, "OK" if base == want else "MISMATCH")
killed = 0
for name, (a, b) in MUTANTS.items():
    assert SRC.count(a) == 1, f"anchor not unique: {name}"
    got = exits(SRC.replace(a, b))
    k = got != want
    killed += k
    print(f"{'killed  ' if k else 'SURVIVED'} {name}: {got}")
print(f"{killed}/{len(MUTANTS)} killed")
