# Sounding Stone

A catalogue of cases where a tool reported success, or reported nothing, and I believed it.

Each entry carries the date, the commands as they were actually run, and the shape of the
error. The recurring subject is machine checks that fail without failing: exit status zero,
a valid response, a confident string, and a conclusion that was never in the data.

**Read it:** https://sounding-stone.github.io

## Entries

| No. | Title | Date |
|-----|-------|------|
| 001 | [Two kinds of 404](index.html) | 2026-09-08 |

## Layout

- `index.html` — the current entry, and the **canonical text**. Single file, no build step,
  no dependencies, no JavaScript.
- `checks/` — runnable artefacts from the entries. Each one ships its own control group and
  refuses to report if the controls fail to separate.
- `posts/` — archive of earlier entries once `index.html` moves on.

There is deliberately one copy of each text. A second copy is a second thing to keep in
sync, and nothing here would detect the drift.

## checks/availability.sh

Domain availability via RDAP, with a known-positive and a known-negative in every batch.

```
$ ./checks/availability.sh soundingstone.dev soundingstone.io soundingstone.com
control +  wikipedia.org                REGISTERED
control -  zzq-nope-19f3a7x.org         FREE

soundingstone.dev              FREE
soundingstone.io               UNMEASURABLE  <- this TLD has no RDAP service; NOT the same as free
soundingstone.com              REGISTERED
```

If the controls come back the same, or come back wrong, it exits 2 without touching the
candidates.

---

Written by Yu Hsien Fang.
