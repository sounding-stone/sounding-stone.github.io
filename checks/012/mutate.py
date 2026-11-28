#!/usr/bin/env python3
"""Break linkguard.py on purpose and check that the target matrix notices."""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "linkguard.py")).read()

def fresh_app():
    out = subprocess.run([os.path.join(HERE, "demo.sh")], capture_output=True, text=True, check=True)
    return out.stdout.strip()

def dangling_app():
    app = fresh_app()
    os.symlink("nowhere", os.path.join(app, "dl"))
    return app

def repo_link_app():
    app = fresh_app()
    w = os.path.dirname(app)
    os.rename(os.path.join(app, "node_modules"), os.path.join(w, "oldlink"))
    os.rename(os.path.join(app, "node_modules.nosync"), os.path.join(app, "node_modules"))
    os.symlink(app, os.path.join(w, "repo-link"))
    return os.path.join(w, "repo-link")

NPM = ["npm", "install", "--no-audit", "--no-fund", "--offline"]
# (label, make cwd, guarded paths, command, expected exit)
MATRIX = [
    ("npm install, node_modules is a link", fresh_app, ["node_modules"], NPM, 1),
    ("npm install, project dir is a link", repo_link_app, ["../repo-link", "node_modules"], NPM, 0),
    ("true", fresh_app, ["node_modules"], ["true"], 0),
    ("replace link and fail", fresh_app, ["node_modules"],
     ["sh", "-c", "rm node_modules && mkdir node_modules && exit 5"], 4),
    ("pnpm install", fresh_app, ["node_modules"], ["pnpm", "install", "--offline"], 0),
    ("missing path gets created", fresh_app, ["newdir"], ["mkdir", "newdir"], 1),
    ("dangling link removed", dangling_app, ["dl"], ["rm", "dl"], 1),
]

MUTANTS = [
    ("islink check removed", '    if os.path.islink(path):\n        return "link -> " + os.readlink(path)\n', ""),
    ("link target not recorded", 'return "link -> " + os.readlink(path)', 'return "link"'),
    ("exit ignores command rc", "return 1 if rc == 0 else 4", "return 1"),
    ("never reports change", "    if not changed:\n        return 0\n", "    return 0\n"),
    ("compares after with after", "changed = any(b != a for _, b, a in rows)", "changed = any(a != a for _, b, a in rows)"),
    ("controls not enforced", "    if not run_controls():", "    if not run_controls() and False:"),
    ("fixture self-check removed", '    if describe(os.path.join(base, "x")) != "link -> store":', "    if False:"),
    ("stat instead of lstat for missing", "        os.lstat(path)\n", "        os.stat(path)\n"),
    ("realpath compared instead", "        after = describe(os.path.join(cwd or \"\", p))",
     "        after = before[p] if os.path.realpath(os.path.join(cwd or '', p)) else 'x'"),
    ("changes inside the link count", 'return "link -> " + os.readlink(path)',
     'return "link -> " + os.readlink(path) + str(sorted(os.listdir(path)))'),
    ("missing path not treated as a state", "    except FileNotFoundError:\n        return \"missing\"\n",
     "    except FileNotFoundError:\n        return \"directory\"\n"),
    ("exit code mapping flattened", "    sys.exit(code)", "    sys.exit(1 if code else 0)"),
]

def run_matrix(script):
    got = []
    for label, make, paths, cmd, want in MATRIX:
        cwd = make()
        rc = subprocess.run([sys.executable, script, *paths, "--", *cmd], cwd=cwd,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        got.append(rc)
    return got

if __name__ == "__main__":
    want = [m[-1] for m in MATRIX]
    with tempfile.TemporaryDirectory() as t:
        base = os.path.join(t, "linkguard.py")
        open(base, "w").write(SRC)
        got = run_matrix(base)
        print(f"original   {got}  {'matches' if got == want else 'DOES NOT MATCH'} {want}")
        if got != want:
            sys.exit(1)
        killed = 0
        for name, old, new in MUTANTS:
            if SRC.count(old) != 1:
                print(f"mutant {name!r}: pattern found {SRC.count(old)} times, fix the mutant")
                sys.exit(3)
            path = os.path.join(t, "mutant.py")
            open(path, "w").write(SRC.replace(old, new))
            g = run_matrix(path)
            dead = g != want
            killed += dead
            print(f"{'killed  ' if dead else 'SURVIVED'} {name:38} {g}")
        print(f"{killed}/{len(MUTANTS)} killed")
