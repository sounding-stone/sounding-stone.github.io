# Sounding Stone

A catalogue of cases where a tool reported success, or reported nothing, and I believed it.

Each entry carries the date, the commands as they were actually run, and the shape of the
error. The recurring subject is machine checks that fail without failing: exit status zero,
a valid response, a confident string, and a conclusion that was never in the data.

**Read it:** https://sounding-stone.github.io

## Entries

| No. | Title | Date |
|-----|-------|------|
| 004 | [yaml ok](posts/004-yaml-ok.html) | 2026-09-25 |
| 003 | [That's all of them](posts/003-thats-all-of-them.html) | 2026-09-18 |
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

## checks/removal.py

Whether deleting one entry from a YAML list changed anything else: REMOVED, DAMAGED or
UNPARSEABLE, with repeated keys treated as fatal and five built-in controls in every run.

```
$ ./checks/removal.py before.yaml watchlist.yaml contract_reply
control +  UNPARSEABLE  orphaned tail, keys shared with neighbour
control +  DAMAGED      orphaned tail, key new to neighbour
control +  UNPARSEABLE  BEFORE already had a duplicate key
control +  DAMAGED      a top-level key outside the list went missing
control -  REMOVED      clean removal

UNPARSEABLE  watchlist.yaml  (removed 'contract_reply' from before.yaml)
             duplicate key 'known_positive' at lines 6 and 9
```

Exits 0 for REMOVED, 1 for DAMAGED or UNPARSEABLE, 2 if the controls fail, and 3 if an input
file cannot be read. The controls cover the classification but not the mapping from verdict
to exit status: forcing that to 0 passes every control.

## checks/exhaustive.py

Whether a paginated result can support an exhaustive claim at all: COMPLETE, TRUNCATED or
UNMEASURABLE per endpoint, with a known-positive and a known-negative fixture in every run.

```
$ ./checks/exhaustive.py items total_count 5 \
    'https://api.github.com/search/repositories?q=stars:%3E390000&per_page={n}' \
    'https://api.github.com/search/repositories?q=stars:%3E395000&per_page={n}'

control +  control-truncated.json   TRUNCATED     fixture, declared total 4210, returned 5
control -  control-complete.json    COMPLETE      fixture, declared total 3, returned 3

TRUNCATED     http 200, declared total 6, returned 5
COMPLETE      http 200, declared total 5, returned 5
```

Exits 1 if anything is TRUNCATED, 2 if the controls fail to separate, and 3 if anything is
UNMEASURABLE. `len(rows) == page_size` with no declared total is UNMEASURABLE, never
COMPLETE: the `n+1` probe can prove truncation but never completeness, because an endpoint
that clamps page size to `n` is indistinguishable from one that holds exactly `n` rows.

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
