# Sounding Stone

A catalogue of cases where a tool reported success, or reported nothing, and I believed it.

Each entry carries the date, the commands as they were actually run, and the shape of the
error. The recurring subject is machine checks that fail without failing: exit status zero,
a valid response, a confident string, and a conclusion that was never in the data.

**Read it:** https://sounding-stone.github.io

## Entries

| No. | Title | Date |
|-----|-------|------|
| 002 | [Everyone came from the homepage](posts/002-everyone-came-from-the-homepage.html) | 2026-09-12 |
| 001 | [Two kinds of 404](posts/001-two-kinds-of-404.html) | 2026-09-08 |

## Layout

- `index.html` — the entry list. No build step, no dependencies, no JavaScript.
- `posts/` — one file per entry, and the **canonical text** of it. Each file is
  self-contained, including its own stylesheet.
- `checks/` — runnable artefacts from the entries. Each one ships its own control group and
  refuses to report if the controls fail to separate.

Entry 001 originally lived at `index.html`, which was also the site root. Moving it into
`posts/` frees the root for the list, so the root no longer serves 001. GitHub Pages cannot
redirect, and the list has to live at the root, so no stub is possible: anyone who
bookmarked the root now gets the list, with 001 one click away.

There is deliberately one copy of each text. A second copy is a second thing to keep in
sync, and nothing here would detect the drift.

## checks/referrer.sh

Whether a path-level referrer from a given origin can reach you at all, with a
known-positive and a known-negative in every run.

```
$ ./checks/referrer.sh en.wikipedia.org www.djangoproject.com techcrunch.com

control +  www.bbc.com                  PATH-VISIBLE  no-referrer-when-downgrade
control -  www.debian.org               NO-REFERRER   no-referrer

en.wikipedia.org             ORIGIN-ONLY   origin-when-cross-origin
www.djangoproject.com        NO-REFERRER   same-origin
techcrunch.com               PATH-VISIBLE  no-referrer-when-downgrade
```

Exits 2 if the controls fail to separate, and 3 if a candidate could not be reached —
unreachable must not share a bucket with "reachable, sets no policy".

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
