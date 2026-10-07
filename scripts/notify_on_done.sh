#!/usr/bin/env bash
# Detached watcher: wait for the DONE marker of a run, then notify.
#   nohup scripts/notify_on_done.sh results/2026-10-06/DONE > /dev/null 2>&1 & disown
MARKER=$1
while [ ! -f "$MARKER" ]; do sleep 20; done
MSG="Run finished: $(cat "$MARKER")"
osascript -e "display notification \"$MSG\" with title \"Arabic OCR bench\" sound name \"Glass\""
afplay /System/Library/Sounds/Glass.aiff
say "Arabic OCR benchmark finished"
