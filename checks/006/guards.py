"""Predicates to point alias_check.py at. Each answers: is `c` the protected file `p`?"""
import os
from pathlib import Path

def string_eq(c, p):   return str(c) == str(p)
def resolve_eq(c, p):  return c.resolve() == p.resolve()            # the fence as first written
def casefold_eq(c, p): return str(c.resolve()).casefold() == str(p.resolve()).casefold()
def samefile(c, p):    return os.path.samefile(c, p)                 # ask the filesystem
def bytes_eq(c, p):    return Path(c).read_bytes() == Path(p).read_bytes()
def always(c, p):      return True
def raises(c, p):      raise OSError("guard crashed")
