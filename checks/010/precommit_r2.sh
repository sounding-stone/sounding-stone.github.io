#!/bin/sh
# P2-01 vault freeze: refuse every commit into the journal-git while the freeze flag exists.
# Covers journal.sh／fleet.sh／a direct `G commit` alike (`--no-verify` bypasses it — disclosed).
F="${VAULT_FREEZE_LOCK:-$HOME/.local/state/vault-freeze/LOCK}"
if [ -e "$F" ] || [ -L "$F" ]; then
  echo "pre-commit: commit refused (vault frozen): $F exists" >&2
  exit 1
fi
exit 0
