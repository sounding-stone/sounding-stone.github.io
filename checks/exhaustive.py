#!/usr/bin/env python3
"""Can this paginated result support an exhaustive claim?

Answers per endpoint: COMPLETE / TRUNCATED / UNMEASURABLE.
Ships a known-positive and a known-negative fixture. If they fail to separate,
it refuses to classify the candidates.

The rule it mechanizes: len(rows) == page_size is never evidence of a total.
It is the one case where "I fetched a slice" and "that is all there is" are
byte-identical, so it is reported as UNMEASURABLE, not as a count.

Exit: 0 all COMPLETE | 1 some TRUNCATED | 2 controls failed | 3 some UNMEASURABLE

usage: exhaustive.py ROWS_KEY TOTAL_KEY|- PAGE_SIZE URL_WITH_{n} ...
"""
import json, pathlib, sys, urllib.error, urllib.request

UA = {"User-Agent": "sounding-stone-exhaustive/1.0", "Accept": "application/json"}


def fetch(url):
    """Return (body_or_None, note). A non-200 must never become an empty page."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            return json.loads(r.read().decode()), ("http %s" % r.status if r.status else "fixture")
    except urllib.error.HTTPError as e:
        return None, f"http {e.code}"
    except Exception as e:
        return None, type(e).__name__


def dig(obj, path):
    for k in path.split("."):
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def classify(url_tmpl, rows_key, total_key, n):
    """Fetch at page size n (and n+1 when needed) and classify."""
    body, note = fetch(url_tmpl.format(n=n))
    if body is None:
        return "UNMEASURABLE", f"{note} - no body to count"

    rows = dig(body, rows_key)
    if not isinstance(rows, list):
        # An error payload parses fine and has no rows. Reporting 0 here is the bug.
        return "UNMEASURABLE", f"{note}, but '{rows_key}' is absent or not a list"
    got = len(rows)

    total = dig(body, total_key) if total_key else None
    if isinstance(total, bool) or not isinstance(total, int):
        total = None

    if total is not None:
        return ("COMPLETE" if got >= total else "TRUNCATED",
                f"{note}, declared total {total}, returned {got}")

    if got < n:
        # "fewer rows than I asked for, so that must be all of them" is the same
        # bug one branch over: an endpoint that clamps page size below the size
        # you requested is indistinguishable from one that has run out of rows.
        # GitHub clamps per_page to 100, so at n=500 this branch once reported
        # COMPLETE for the same query whose declared total was 251.
        return ("UNMEASURABLE",
                f"{note}, returned {got} < page size {n} and nothing declares a total "
                f"- ran-out-of-rows and page-size-clamped-below-{n} are indistinguishable")

    # got == n and nothing declares a total: probe one past the edge.
    body2, note2 = fetch(url_tmpl.format(n=n + 1))
    rows2 = dig(body2, rows_key) if body2 is not None else None
    if not isinstance(rows2, list):
        return "UNMEASURABLE", f"{note}, returned exactly {got}; probe at {n+1} failed ({note2})"
    if len(rows2) > got:
        return "TRUNCATED", f"{note}, returned {got}; page size {n+1} returned {len(rows2)}"
    # The probe has its own invisible ceiling. If asking for n+1 returns n again,
    # "there are exactly n" and "this endpoint clamps page size to n" are
    # indistinguishable -- GitHub clamps per_page to 100, so at n=100 this branch
    # once reported COMPLETE for a query whose declared total was 251.
    return ("UNMEASURABLE",
            f"{note}, returned {got}; page size {n+1} also returned {len(rows2)} "
            f"- exactly-{got} and page-size-clamped-at-{got} are indistinguishable")


HERE = pathlib.Path(__file__).resolve().parent
CONTROL_POS = "control-truncated.json"   # must classify TRUNCATED
CONTROL_NEG = "control-complete.json"    # must classify COMPLETE


def control(name):
    return (HERE / name).as_uri()


def main(argv):
    if len(argv) < 5:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    rows_key, total_key, n = argv[1], (None if argv[2] == "-" else argv[2]), int(argv[3])
    candidates = argv[4:]

    cp, cpn = classify(control(CONTROL_POS), "rows", "total", 5)
    cn, cnn = classify(control(CONTROL_NEG), "rows", "total", 5)
    print(f"control +  {CONTROL_POS:<24} {cp:<13} {cpn}")
    print(f"control -  {CONTROL_NEG:<24} {cn:<13} {cnn}\n")
    if cp != "TRUNCATED" or cn != "COMPLETE":
        sys.stdout.flush()
        print(f"controls did not separate: + is {cp}, - is {cn}", file=sys.stderr)
        print("refusing to classify candidates.", file=sys.stderr)
        return 2

    worst = 0
    for url in candidates:
        verdict, note = classify(url, rows_key, total_key, n)
        print(f"{verdict:<13} {note}\n              {url.format(n=n)}")
        worst = max(worst, {"COMPLETE": 0, "TRUNCATED": 1, "UNMEASURABLE": 3}[verdict])
    print("\nTRUNCATED or UNMEASURABLE cannot support 'all', 'only' or 'the rest are'.")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
