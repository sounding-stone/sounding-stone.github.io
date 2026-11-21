#!/usr/bin/env python3
"""Does a cleanup command and the check that confirms it share a blind spot?

usage: cleanup_check.py CLEAN_CMD COUNT_CMD
  {root} = the directory, spelled the way your command would spell it
  {pat}  = the pattern of the things to remove, quoted (for find -name)
  {glob} = the same pattern unquoted (for the shell to expand)
  COUNT_CMD must print the number of matches left; its last integer is read.
Exit: 0 every fixture cleaned and the count agreed | 1 the count said 0 while
targets were still there | 4 cleanup failed or over-deleted, but no false 0 |
2 the built-in controls did not come out as expected | 3 usage or fixture error.
The oracle lists os.path.realpath(root) with os.listdir and fnmatch, so it does
not share find's or the shell's way of looking.
"""
import fnmatch, os, re, shlex, subprocess, sys, tempfile

PAT = "proj-*"
TARGETS = ["proj-1", "proj-2", "proj-3", "proj-x y"]
DECOYS = ["keep-1", "projX"]

def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(3)

def oracle(root):
    return [n for n in os.listdir(os.path.realpath(root)) if fnmatch.fnmatchcase(n, PAT)]

def fixtures(base):
    real = os.path.join(base, "real-dir")
    os.mkdir(real)
    linked_target = os.path.join(base, "private-tmp")
    os.mkdir(linked_target)
    link = os.path.join(base, "tmp")
    os.symlink("private-tmp", link)
    out = [("real directory", real), ("root is a symlink", link)]
    for name, root in out:
        for n in TARGETS + DECOYS:
            os.mkdir(os.path.join(os.path.realpath(root), n))
        if sorted(oracle(root)) != sorted(TARGETS):
            fail(f"fixture error: {name} does not hold the targets it should")
    if not os.path.islink(link):
        fail("fixture error: symlink fixture is not a symlink")
    return out

def run(cmd, root):
    c = cmd.replace("{root}", shlex.quote(root)).replace("{pat}", shlex.quote(PAT)).replace("{glob}", PAT)
    return subprocess.run(["/bin/sh", "-c", c], capture_output=True, text=True)

def verdict(clean, count, root):
    run(clean, root)
    nums = re.findall(r"\d+", run(count, root).stdout)
    if not nums:
        return "NO-COUNT"
    said, left = int(nums[-1]), len(oracle(root))
    decoys = [d for d in DECOYS if os.path.isdir(os.path.join(os.path.realpath(root), d))]
    if said == 0 and left > 0:
        return f"FALSE-CLEAN   count said 0, {left} still there"
    if len(decoys) != len(DECOYS):
        return f"OVER-DELETE   removed {len(DECOYS) - len(decoys)} thing(s) that did not match"
    if left == 0 and said == 0:
        return "ok"
    return f"NOT-CLEAN     count said {said}, {left} still there"

def check(clean, count):
    with tempfile.TemporaryDirectory(dir=os.environ.get("CHECK_TMP")) as base:
        return [(name, verdict(clean, count, root)) for name, root in fixtures(base)]

def worst(rows):
    for tag in ("FALSE-CLEAN", "NOT-CLEAN", "OVER-DELETE", "NO-COUNT"):
        if any(v.startswith(tag) for _, v in rows):
            return tag
    return "ok"

FIND_DEL = "find {root} -maxdepth 1 -name {pat} -delete"
FIND_CNT = "find {root} -maxdepth 1 -name {pat} | wc -l"
LS_CNT = "ls -d {root}/{glob} 2>/dev/null | wc -l"
CONTROLS = [
    ("find deletes, same find counts", FIND_DEL, FIND_CNT, "FALSE-CLEAN"),
    ("find deletes, ls counts", FIND_DEL, LS_CNT, "NOT-CLEAN"),
    ("nothing deleted, count is echo 0", "true", "echo 0", "FALSE-CLEAN"),
    ("glob rmdir, ls counts", "rmdir {root}/{glob}", LS_CNT, "ok"),
    ("find with trailing slash, same find counts",
     "find {root}/ -maxdepth 1 -name {pat} -delete", "find {root}/ -maxdepth 1 -name {pat} | wc -l", "ok"),
]

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(3)
    bad = False
    for label, cl, co, want in CONTROLS:
        got = worst(check(cl, co))
        print(f"control {'OK   ' if got == want else 'WRONG'} {label}: {got}")
        bad |= got != want
    if bad:
        print("controls did not separate; not judging the target")
        sys.exit(2)
    rows = check(sys.argv[1], sys.argv[2])
    w = worst(rows)
    print("OK" if w == "ok" else w)
    for name, v in rows:
        print(f"  {'ok ' if v == 'ok' else 'BAD'} {name:18} {v}")
    sys.exit({"ok": 0, "FALSE-CLEAN": 1}.get(w, 4))
