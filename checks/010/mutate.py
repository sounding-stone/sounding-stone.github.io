# Break failopen.py one way at a time. A mutant is caught if, on either target,
# it gives a different first verdict word or a different exit status.
import subprocess, sys, pathlib
SRC = pathlib.Path("failopen.py").read_text()
MUTANTS = [
    ("no chmod on the unreadable parent", "        os.chmod(d, 0)\n", "        pass\n"),
    ("loop fixture is a plain directory", 'os.symlink("loop", d)', "os.mkdir(d)"),
    ("absent counts as should-refuse", '"FLAG"), errno.ENOENT, False))', '"FLAG"), errno.ENOENT, True))'),
    ("can't-look rows never count", "else: bad_unknown = True", "else: pass"),
    ("ENOENT row counted as can't-look", "if want_errno in (None, errno.ENOENT)", "if want_errno in (None,)"),
    ("only exit 1 means refused", "refused = r.returncode != 0", "refused = r.returncode == 1"),
    ("flag path not substituted", 'a.replace("{}", flag)', "a"),
    ("every verdict exits 0", 'sys.exit(0 if got == "OK" else 1)', "sys.exit(0)"),
    ("fixture lstat self-check off", "if got != want_errno:", "if False:"),
    ("controls not enforced", "if bad:", "if False:"),
]
TARGETS = [["env", "VAULT_FREEZE_LOCK={}", "sh", "precommit_r2.sh"],
           ["env", "VAULT_FREEZE_LOCK={}", "sh", "precommit_r3.sh"]]
def run(f, t):
    r = subprocess.run([sys.executable, "-I", f, *t], capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if l and not l.startswith(("control ", "  "))]
    word = (last[-1].split()[0] if last else (r.stderr.strip().split()[0] if r.stderr.strip() else "-"))
    return f"{r.returncode} {word}"
base = [run("failopen.py", t) for t in TARGETS]
print("original:", " | ".join(base))
caught = 0
for name, a, b in MUTANTS:
    if a not in SRC:
        print("NOT APPLIED", name); continue
    pathlib.Path("mutant.py").write_text(SRC.replace(a, b, 1))
    got = [run("mutant.py", t) for t in TARGETS]
    hit = got != base; caught += hit
    print(f"{'caught  ' if hit else 'SURVIVED'}  {name:<36} {' | '.join(got)}")
pathlib.Path("mutant.py").unlink()
print(f"\n{len(MUTANTS)} mutants, {caught} caught, {len(MUTANTS) - caught} survived")
