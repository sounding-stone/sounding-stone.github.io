#!/bin/sh
# P2-01 vault freeze: refuse every commit into the journal-git while the freeze flag exists.
# Covers journal.sh／fleet.sh／a direct `G commit` alike (`--no-verify` bypasses it — disclosed).
# Fail-closed (Astra-26 B1): a flag lookup error other than ENOENT refuses too.
F="${VAULT_FREEZE_LOCK:-$HOME/.local/state/vault-freeze/LOCK}"
# P2-01 freeze probe, fail-closed (Astra-26 B1) — the same text in journal.sh／fleet.sh／run-pipeline.sh／
# journal-git pre-commit. FREEZE_STATE＝absent (lstat ENOENT only)｜present (lstat ok; a dangling symlink
# too)｜<errno name> (any other lookup error ⇒ the caller refuses). `[ -e ]`／`[ -L ]` cannot tell ENOENT
# from EACCES／ENOTDIR／EIO, so a miss asks /usr/bin/stat (lstat(2) by default; absolute path, no vault
# file, no venv; one exec ≈1 ms, only when no flag is visible) and matches its exact ENOENT line.
freeze_probe() {
  FREEZE_STATE=present
  if [ -e "$1" ] || [ -L "$1" ]; then return 0; fi
  [ -x /usr/bin/stat ] || { FREEZE_STATE=ENOSTAT; return 0; }
  if _fz_err="$(LC_ALL=C /usr/bin/stat -f %i -- "$1" 2>&1 >/dev/null)"; then return 0; fi
  case "$_fz_err" in
    "stat: $1: stat: No such file or directory") FREEZE_STATE=absent ;;
    *": Permission denied") FREEZE_STATE=EACCES ;;
    *": Operation not permitted") FREEZE_STATE=EPERM ;;
    *": Not a directory") FREEZE_STATE=ENOTDIR ;;
    *": Input/output error") FREEZE_STATE=EIO ;;
    *": Too many levels of symbolic links") FREEZE_STATE=ELOOP ;;
    *": File name too long") FREEZE_STATE=ENAMETOOLONG ;;
    *) FREEZE_STATE=EUNKNOWN ;;
  esac
}
freeze_probe "$F"
case "$FREEZE_STATE" in
  absent) exit 0 ;;
  present) echo "pre-commit: commit refused (vault frozen): $F exists" >&2 ;;
  *) echo "FAILED (vault freeze state unknown): $F — $FREEZE_STATE; refusing (pre-commit: commit refused)" >&2 ;;
esac
exit 1
