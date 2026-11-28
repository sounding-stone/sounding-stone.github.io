#!/usr/bin/env python3
"""Run a command and report whether it changed what a path *is*.

usage: linkguard.py PATH [PATH ...] -- COMMAND [ARG ...]

Before and after COMMAND, each PATH is described with os.lstat and
os.readlink: missing, file, directory, or a symbolic link and where it points.
The command's own output and exit code are not used to decide anything.

Exit: 0 every PATH is what it was | 1 a PATH changed and COMMAND exited 0 |
4 a PATH changed and COMMAND failed | 2 the built-in controls did not come
out as expected | 3 usage error.
Changing files inside a linked directory does not count as a change.
"""
import os, subprocess, sys, tempfile

def describe(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return "missing"
    if os.path.islink(path):
        return "link -> " + os.readlink(path)
    if os.path.isdir(path):
        return "directory"
    return "file"

def guard(paths, cmd, cwd=None, quiet=False):
    before = {p: describe(os.path.join(cwd or "", p)) for p in paths}
    out = subprocess.DEVNULL if quiet else None
    try:
        rc = subprocess.run(cmd, cwd=cwd, stdout=out, stderr=out).returncode
    except OSError as e:
        print(f"cannot run {cmd[0]!r}: {e.strerror}", file=sys.stderr)
        sys.exit(3)
    rows = []
    for p in paths:
        after = describe(os.path.join(cwd or "", p))
        rows.append((p, before[p], after))
    return rc, rows

def verdict(rc, rows):
    changed = any(b != a for _, b, a in rows)
    if not changed:
        return 0
    return 1 if rc == 0 else 4

def fixture(base):
    os.mkdir(os.path.join(base, "store"))
    os.mkdir(os.path.join(base, "other"))
    os.symlink("store", os.path.join(base, "x"))
    if describe(os.path.join(base, "x")) != "link -> store":
        print("fixture error: could not make a symbolic link", file=sys.stderr)
        sys.exit(3)

CONTROLS = [
    ("link replaced by a directory, exit 0", ["sh", "-c", "rm x && mkdir x"], 1),
    ("nothing happens", ["true"], 0),
    ("a file is written through the link", ["sh", "-c", "touch x/new"], 0),
    ("link pointed somewhere else", ["ln", "-sfn", "other", "x"], 1),
    ("link replaced, command fails", ["sh", "-c", "rm x && mkdir x && exit 7"], 4),
]

def run_controls():
    ok = True
    for label, cmd, want in CONTROLS:
        with tempfile.TemporaryDirectory() as base:
            fixture(base)
            got = verdict(*guard(["x"], cmd, cwd=base, quiet=True))
        print(f"control {'OK   ' if got == want else 'WRONG'} {label}: exit {got}")
        ok &= got == want
    return ok

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    args = sys.argv[1:]
    if "--" not in args or args.index("--") == 0 or args[-1] == "--":
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(3)
    i = args.index("--")
    paths, cmd = args[:i], args[i + 1:]
    if not run_controls():
        print("controls did not separate; not judging the command")
        sys.exit(2)
    rc, rows = guard(paths, cmd)
    code = verdict(rc, rows)
    print(f"command exit {rc}")
    for p, b, a in rows:
        print(f"  {'kept   ' if b == a else 'CHANGED'} {p}: {b}" + ("" if b == a else f"  =>  {a}"))
    sys.exit(code)
