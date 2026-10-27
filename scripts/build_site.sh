#!/usr/bin/env bash
# Copies only the files the website needs into dist/ for deployment.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist
mkdir dist
cp -r index.html styles.css favicon.ico assets fonts dist/
