# Price Watcher Setup (Manual)

This document explains how to set up the project on a new Ubuntu 24.04 system and configure daily scheduled price checks with systemd.

## Quick Start
Run the setup.sh script which automates all steps:

```bash
bash setup.sh
```

For a manual setup, follow the steps below.

## 1) Prepare the environment
From the project root:

```bash
python3 -m venv .venv
./.venv/bin/python -V
```

No external Python packages are required.

## 2) Create .env
Create a file `.env` in the project root:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

See [README.md](README.md) for instructions on obtaining these values.

## 3) Test run
From the project root:

```bash
./.venv/bin/python execution/price_watch.py --force-notify
```

You should receive a Telegram message.

## 4) Systemd user service and timer
The repo includes ready-to-copy unit files in `systemd/`:
- `systemd/price-watch.service`
- `systemd/price-watch.timer`

Create the systemd user directory if needed:

```bash
mkdir -p ~/.config/systemd/user
```

Copy the unit files:

```bash
cp systemd/price-watch.service ~/.config/systemd/user/
cp systemd/price-watch.timer ~/.config/systemd/user/
```

Update the absolute paths in the service file to match your installation (see placeholders comment in the file).

Enable the timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now price-watch.timer
systemctl --user list-timers --all | grep price-watch
```

Enable the timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now price-watch.timer
systemctl --user list-timers --all | grep price-watch
```

Disable the timer (when you no longer need it):

```bash
systemctl --user disable --now price-watch.timer
```

### Helper script (optional)
The repo includes `price-watch-timer.sh` to manage the timer:

```bash
chmod +x price-watch-timer.sh
./price-watch-timer.sh --print
./price-watch-timer.sh --enable
./price-watch-timer.sh --disable
```

## Troubleshooting
- Logs: `journalctl --user -u price-watch.service --since today`
- Manual run: `./.venv/bin/python execution/price_watch.py`
- Parsing fails: check the page URL and HTML changes
