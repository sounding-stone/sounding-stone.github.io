import fcntl, hashlib, sys, time
from pathlib import Path
def key(p): return Path("locks") / (hashlib.sha256(str(Path(p).resolve()).encode()).hexdigest()[:12] + ".lock")
p = sys.argv[1]; h = open(key(p), "a+")
try:
    fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); print(f"{p}: lock acquired ({key(p).name})", flush=True); time.sleep(2)
except BlockingIOError:
    print(f"{p}: busy ({key(p).name})", flush=True)
