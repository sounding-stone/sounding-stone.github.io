#!/bin/sh
# Builds a throwaway project whose node_modules is a symbolic link to node_modules.nosync,
# installed from a local tarball (no network). Prints the directory it made.
set -e
W=$(mktemp -d)
mkdir "$W/pkg" "$W/app"
cd "$W/pkg"
printf '{"name":"tinypkg","version":"1.0.0","main":"index.js"}' > package.json
echo 'module.exports = 1' > index.js
npm pack --silent >/dev/null
cd "$W/app"
printf '{"name":"app","version":"1.0.0"}' > package.json
npm install --no-audit --no-fund --offline ../pkg/tinypkg-1.0.0.tgz >/dev/null 2>&1
mv node_modules node_modules.nosync
ln -s node_modules.nosync node_modules
echo "$W/app"
