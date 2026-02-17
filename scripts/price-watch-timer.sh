#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: price-watch-timer.sh [option]

Options:
  -e, --enable   Enable timer.
  -d, --disable  Disable timer.
  -p, --print    Print timer.
  -h, --help     Prints this usage.
USAGE
}

if [[ $# -eq 0 ]]; then
  usage
  exit 0
fi

case "$1" in
  -e|--enable)
    systemctl --user daemon-reload
    systemctl --user enable --now price-watch.timer
    ;;
  -d|--disable)
    systemctl --user disable --now price-watch.timer
    ;;
  -p|--print)
    systemctl --user list-timers --all | grep price-watch || true
    systemctl --user status price-watch.timer --no-pager
    ;;
  -h|--help)
    usage
    ;;
  *)
    echo "Unknown option: $1" >&2
    usage
    exit 1
    ;;
esac
