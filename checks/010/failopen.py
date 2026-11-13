#!/usr/bin/env python3
"""Does a guard refuse when it cannot look at its flag?

usage: failopen.py CMD [ARG ...]   (any argument may contain {} = the flag path)
The command is the guard: exit 0 = "no flag, go ahead"; any other exit = "refuse".
Each fixture is checked with os.lstat first, so a fixture that is not what it
claims to be stops the run instead of producing a verdict.
"""
import errno, os, subprocess, sys, tempfile

def fixtures(root):
    """(name, flag path, errno lstat must give or None for 'found', guard should refuse)"""
    out = []
    d = os.path.join(root, "absent"); os.mkdir(d)
    out.append(("absent", os.path.join(d, "FLAG"), errno.ENOENT, False))
    d = os.path.join(root, "present"); os.mkdir(d); open(os.path.join(d, "FLAG"), "w").close()
    out.append(("present", os.path.join(d, "FLAG"), None, True))
    d = os.path.join(root, "dangling"); os.mkdir(d); os.symlink("nowhere", os.path.join(d, "FLAG"))
    out.append(("dangling symlink", os.path.join(d, "FLAG"), None, True))
    d = os.path.join(root, "loop"); os.symlink("loop", d)
    out.append(("parent is a symlink loop", os.path.join(d, "FLAG"), errno.ELOOP, True))
    if os.geteuid() != 0:  # root ignores directory permissions
        d = os.path.join(root, "unreadable"); os.mkdir(d); open(os.path.join(d, "FLAG"), "w").close()
        os.chmod(d, 0)
        out.append(("parent not searchable", os.path.join(d, "FLAG"), errno.EACCES, True))
    return out

def lstat_errno(path):
    try:
        os.lstat(path)
    except OSError as e:
        return e.errno
    return None

def verdict(cmd):
    rows, bad_normal, bad_unknown = [], False, False
    with tempfile.TemporaryDirectory() as root:
        try:
            for name, flag, want_errno, should_refuse in fixtures(root):
                got = lstat_errno(flag)
                if got != want_errno:
                    print(f"fixture '{name}': lstat gave {got}, expected {want_errno}; not testing"); sys.exit(3)
                r = subprocess.run([a.replace("{}", flag) for a in cmd], capture_output=True)
                refused = r.returncode != 0
                ok = refused == should_refuse
                if not ok:
                    if want_errno in (None, errno.ENOENT): bad_normal = True
                    else: bad_unknown = True
                rows.append(f"  {'ok ' if ok else 'BAD'} {name:<25} {'refused' if refused else 'allowed'}")
        finally:
            u = os.path.join(root, "unreadable")
            if os.path.lexists(u): os.chmod(u, 0o755)
    if os.geteuid() == 0: rows.append("  --  parent not searchable    skipped: running as root")
    return ("WRONG" if bad_normal else "FAIL-OPEN" if bad_unknown else "OK"), rows

PY = sys.executable
CONTROLS = [
    ("os.path.lexists", "FAIL-OPEN", [PY, "-c", "import os,sys; sys.exit(1 if os.path.lexists(sys.argv[1]) else 0)", "{}"]),
    ("[ -e ] || [ -L ]", "FAIL-OPEN", ["sh", "-c", '[ -e "$1" ] || [ -L "$1" ] && exit 1; exit 0', "_", "{}"]),
    ("lstat, only ENOENT allows", "OK", [PY, "-c", "import os,sys\ntry: os.lstat(sys.argv[1])\nexcept FileNotFoundError: sys.exit(0)\nexcept (OSError, ValueError): pass\nsys.exit(1)", "{}"]),
    ("same, refusing with exit 78", "OK", [PY, "-c", "import os,sys\ntry: os.lstat(sys.argv[1])\nexcept FileNotFoundError: sys.exit(0)\nexcept (OSError, ValueError): pass\nsys.exit(78)", "{}"]),
    ("always allows", "WRONG", ["true"]),
    ("always refuses", "WRONG", ["false"]),
]

if len(sys.argv) < 2:
    print(__doc__); sys.exit(3)
bad = 0
for label, want, cmd in CONTROLS:
    got, _ = verdict(cmd)
    bad += got != want
    print(f"control  {got:<9} {label}" + ("" if got == want else f"  <- want {want}"))
if bad:
    print(f"\ncontrols failed ({bad}); not checking your guard"); sys.exit(2)
got, rows = verdict(sys.argv[1:])
print(f"\n{got}  {' '.join(sys.argv[1:])}"); print("\n".join(rows))
sys.exit(0 if got == "OK" else 1)
