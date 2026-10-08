#!/usr/bin/env python3
"""alias_check.py -- does your "is this the protected file?" predicate see through aliases?

usage: python3 alias_check.py FILE.py:FUNCTION
  FUNCTION(candidate: Path, protected: Path) -> bool   (True = "this is the protected file")

Builds one protected file in a fresh temp directory and asks the predicate about
spellings that open that same file (the answer must be True) and about files that
are not it (the answer must be False). Same-file is known by construction, never by
asking the filesystem whether two paths are the same: a fresh directory holds
exactly one file, so any spelling that opens it can only be that file.
exit 0 = every answer right; 1 = at least one wrong; 2 = usage error.
"""
import importlib.util, os, sys, tempfile, unicodedata
from pathlib import Path

def load(spec):
    path, _, name = spec.rpartition(":")
    if not path or not name:
        print("usage: alias_check.py FILE.py:FUNCTION"); sys.exit(2)
    mod = importlib.util.spec_from_file_location("guard", path)
    m = importlib.util.module_from_spec(mod); mod.loader.exec_module(m)
    return getattr(m, name)

def cases(base):
    d = base / unicodedata.normalize("NFC", "Café") / "Tasks"; d.mkdir(parents=True)
    p = d / "Main.md"; p.write_text("- [ ] one\n")
    same, other = {"exact": p}, {}
    (base / "link.md").symlink_to(p); same["symlink"] = base / "link.md"
    (base / "dirlink").symlink_to(d, target_is_directory=True); same["symlinked parent"] = base / "dirlink" / "Main.md"
    same["dot-dot"] = d / ".." / "Tasks" / "Main.md"
    os.link(p, base / "hard.md"); same["hard link"] = base / "hard.md"
    variants = {"case": Path(str(p).replace("Café/Tasks/Main.md", "cAFÉ/tASKS/mAIN.MD")),
                "unicode (NFD)": Path(str(p).replace("Café", unicodedata.normalize("NFD", "Café")))}
    for name, v in variants.items():
        if v.exists(): same[name] = v          # this volume opens it -> it is p
        else: print(f"skip  {name:19} this volume does not open that spelling")
    (d / "Other.md").write_text("- [ ] two\n"); other["sibling"] = d / "Other.md"
    (base / "copy.md").write_bytes(p.read_bytes()); other["byte-identical copy"] = base / "copy.md"
    return p, same, other

def main():
    if len(sys.argv) != 2: print("usage: alias_check.py FILE.py:FUNCTION"); return 2
    guard = load(sys.argv[1]); wrong = 0
    with tempfile.TemporaryDirectory() as t:
        p, same, other = cases(Path(t))
        for want, group in ((True, same), (False, other)):
            for name, c in group.items():
                try: got = bool(guard(c, p))
                except Exception as e: got = f"{type(e).__name__}"
                ok = got is want; wrong += not ok
                print(f"{'ok  ' if ok else 'MISS'}  {name:19} -> {got!s:5} (want {want})")
    print("verdict:", "every answer right" if not wrong else f"{wrong} wrong")
    return 1 if wrong else 0

if __name__ == "__main__":
    sys.exit(main())
