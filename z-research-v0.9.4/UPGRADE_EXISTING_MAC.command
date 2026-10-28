#!/bin/bash
# Migrate prior Z-Research or QuantResearch data to this v0.9.3 folder safely.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
printf '\n Z-Research v0.9.3 · Data migration\n --------------------------------\n'
echo "New application folder: $SRC"
read -r -p "Path to OLD application's folder (e.g. ~/Downloads/z-research-old): " FROM
FROM="${FROM/#\~/$HOME}"
if [ ! -d "$FROM/local_data" ]; then
  echo 'ERROR: No local_data directory in that path. Nothing was copied.'
  read -r -p 'Press Enter to close...' || true
  exit 1
fi
FROM="$(cd "$FROM" && pwd)"
if [ "$FROM" = "$SRC" ]; then
  echo 'Same folder; no migration necessary.'
  read -r -p 'Press Enter to close...' || true
  exit 0
fi
if [ -d "$SRC/local_data" ] && [ -n "$(ls -A "$SRC/local_data" 2>/dev/null)" ]; then
  echo 'Destination local_data contains files. Migration stopped to prevent overwriting.'
  echo 'Please back up and reconcile the data folders manually.'
  read -r -p 'Press Enter to close...' || true
  exit 1
fi
mkdir -p "$SRC/local_data"
cp -R "$FROM/local_data/." "$SRC/local_data/"
echo 'Research datasets, analyses and account DB copied. Original untouched.'
echo 'Next: double-click START_MAC.command in the new app folder.'
read -r -p 'Press Enter to close...' || true
