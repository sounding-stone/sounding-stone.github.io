#!/bin/zsh
# Faithful replay of the 2026-11-13 cleanup, with ./tmp (a symlink) standing in for /tmp
# and ./T standing in for $TMPDIR. Run from the fixture directory.
T=$PWD/T
print -r -- '$ find tmp "$T" -maxdepth 1 -name '"'"'proj-*'"'"' | wc -l'
find tmp "$T" -maxdepth 1 -name 'proj-*' | wc -l
print -r -- '$ find tmp "$T" -maxdepth 1 -name '"'"'proj-*'"'"' -exec rm -rf {} +; echo left=$(find tmp "$T" -maxdepth 1 -name '"'"'proj-*'"'"' | wc -l)'
find tmp "$T" -maxdepth 1 -name 'proj-*' -exec rm -rf {} +; echo left=$(find tmp "$T" -maxdepth 1 -name 'proj-*' | wc -l)
print -r -- '$ ls -d tmp/proj-* | wc -l'
ls -d tmp/proj-* | wc -l
print -r -- '$ ls -d "$T"/proj-* | wc -l'
ls -d "$T"/proj-* 2>&1 | wc -l
