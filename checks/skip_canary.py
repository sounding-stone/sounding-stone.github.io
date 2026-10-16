#!/usr/bin/env python3
"""Does a lint layer actually fire, with the config that is really in use?
Runs CMD twice against CONFIG (the live file, never a copy):
  POSITIVE input: must exit exactly 1 AND print EXPECT (the tag of the layer under test)
  NEGATIVE input: must exit 0
Anything else is a REJECT. Prints both outputs so a skip line can't hide."""
import argparse, shlex, subprocess, sys

def run(cmd, inp, config):
    argv = [a.format(input=inp, config=config) for a in shlex.split(cmd)]
    r = subprocess.run(argv, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help="command with {input} and {config}")
    ap.add_argument("--config", required=True)
    ap.add_argument("--positive", required=True)
    ap.add_argument("--negative", required=True)
    ap.add_argument("--expect", required=True, help="tag the layer prints when it fires")
    a = ap.parse_args()
    problems = []
    rc, out = run(a.cmd, a.positive, a.config)
    print(f"positive rc={rc}\n  " + out.replace("\n", "\n  "))
    if rc != 1:
        problems.append(f"positive exited {rc}, not 1: the layer did not fire")
    elif a.expect not in out:
        problems.append(f"positive failed, but not with {a.expect}: a different check fired")
    rc, out = run(a.cmd, a.negative, a.config)
    print(f"negative rc={rc}\n  " + out.replace("\n", "\n  "))
    if rc != 0:
        problems.append(f"negative exited {rc}: the lint fails on clean input")
    for p in problems:
        print("REJECT:", p)
    if not problems:
        print("ACCEPT: the layer fires on the known positive and stays quiet on the negative")
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
