#!/usr/bin/env bash
# Domain availability check that ships its own control group.
#
# Usage:  ./availability.sh name1.dev name2.org ...
#
# The two CONTROL_* rows are the point. If they do not come back
# different, this check cannot tell you anything and says so.

set -uo pipefail

CONTROL_POSITIVE="wikipedia.org"          # certainly registered
CONTROL_NEGATIVE="zzq-nope-19f3a7x.org"   # certainly not

probe() {
  local body
  body=$(curl -sL --max-time 10 "https://rdap.org/domain/$1" 2>/dev/null)
  if   [ -z "$body" ];                              then echo "NO_RESPONSE"
  elif grep -q '"ldhName"'   <<<"$body";            then echo "REGISTERED"
  elif grep -qi 'No RDAP service' <<<"$body";       then echo "UNMEASURABLE"
  elif grep -q '"errorCode"' <<<"$body";            then echo "FREE"
  else                                                   echo "UNPARSED"
  fi
}

pos=$(probe "$CONTROL_POSITIVE")
neg=$(probe "$CONTROL_NEGATIVE")
printf 'control +  %-28s %s\n' "$CONTROL_POSITIVE" "$pos"
printf 'control -  %-28s %s\n' "$CONTROL_NEGATIVE" "$neg"

if [ "$pos" != "REGISTERED" ] || [ "$neg" != "FREE" ]; then
  echo
  echo "CHECK IS DEAD: controls did not separate (+ expected REGISTERED, - expected FREE)."
  echo "Nothing below would be readable. Not running the candidates."
  exit 2
fi

echo
for d in "$@"; do
  r=$(probe "$d")
  case "$r" in
    UNMEASURABLE) note="  <- this TLD has no RDAP service; NOT the same as free" ;;
    NO_RESPONSE|UNPARSED) note="  <- pipe problem, not an answer" ;;
    *) note="" ;;
  esac
  printf '%-30s %s%s\n' "$d" "$r" "$note"
done
