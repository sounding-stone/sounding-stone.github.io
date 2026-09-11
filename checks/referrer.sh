#!/usr/bin/env bash
# Can a path-level referrer from this origin even reach you?
# Answers per referring origin: PATH-VISIBLE / ORIGIN-ONLY / NO-REFERRER.
# Ships a known-positive and a known-negative. If they fail to separate, it
# refuses to classify the candidates.
set -u

CONTROL_POS="${SS_CONTROL_POS:-www.bbc.com}"        # expect PATH-VISIBLE
CONTROL_NEG="${SS_CONTROL_NEG:-www.debian.org}"     # expect NO-REFERRER

# last recognised token wins, per the Referrer Policy spec
policy_of() {
  local host="$1" body hdr meta tok=""
  # reachability first: an unreachable host must not land in the same bucket
  # as a reachable host that sets no policy.
  body=$(curl -sS -m 15 -L -w '\n%{http_code}' "https://$host" 2>/dev/null) \
    || { echo UNREACHABLE; return; }
  [ "$(printf '%s' "$body" | tail -1)" -ge 200 ] 2>/dev/null \
    || { echo UNREACHABLE; return; }
  hdr=$(curl -sSI -m 15 -L "https://$host" 2>/dev/null | tr -d '\r' \
        | awk 'BEGIN{IGNORECASE=1}/^referrer-policy:/{sub(/^[^:]*: */,"");print}' | tail -1)
  meta=$(printf '%s' "$body" | LC_ALL=C tr 'A-Z' 'a-z' | LC_ALL=C tr -d '\n' \
        | grep -oE '<meta[^>]+name=.referrer.[^>]*>' | tail -1 \
        | grep -oE 'content=.[a-z-]+' | cut -d= -f2 | tr -d "\"'")
  for t in $(echo "${meta:-$hdr}" | tr ',' ' '); do
    case "$t" in
      no-referrer|no-referrer-when-downgrade|origin|origin-when-cross-origin|\
      same-origin|strict-origin|strict-origin-when-cross-origin|unsafe-url) tok="$t";;
    esac
  done
  echo "$tok"
}

classify() {
  case "$1" in
    no-referrer-when-downgrade|unsafe-url)                 echo PATH-VISIBLE;;
    no-referrer|same-origin)                               echo NO-REFERRER;;
    origin|origin-when-cross-origin|strict-origin|\
    strict-origin-when-cross-origin)                       echo ORIGIN-ONLY;;
    UNREACHABLE) echo UNREACHABLE;;
    "")  echo ORIGIN-ONLY;;   # no policy set -> modern browser default
    *)   echo UNKNOWN;;
  esac
}

verdict() { printf '%-28s %-13s %s\n' "$1" "$(classify "$2")" "${2:-<no policy set>}"; }
fail=0

p=$(policy_of "$CONTROL_POS"); n=$(policy_of "$CONTROL_NEG")
cp=$(classify "$p");            cn=$(classify "$n")
printf 'control +  '; verdict "$CONTROL_POS" "$p"
printf 'control -  '; verdict "$CONTROL_NEG" "$n"
echo
if [ "$cp" != "PATH-VISIBLE" ] || [ "$cn" = "PATH-VISIBLE" ] || [ "$cp" = "$cn" ]; then
  echo "controls did not separate: + is $cp, - is $cn" >&2
  echo "refusing to classify candidates." >&2
  exit 2
fi

for host in "$@"; do
  pol=$(policy_of "$host"); verdict "$host" "$pol"
  case "$(classify "$pol")" in PATH-VISIBLE|ORIGIN-ONLY|NO-REFERRER) ;; *) fail=1;; esac
done
echo
echo "ORIGIN-ONLY and NO-REFERRER origins cannot support any path-level claim."
echo "A bare origin in a referrer report is not a landing on that origin's root."
[ "$fail" -eq 0 ] || { echo "at least one candidate could not be classified." >&2; exit 3; }
