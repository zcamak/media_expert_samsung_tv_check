# Price Watcher

Monitor product price on a website daily and get Telegram notifications when the price changes.

## Features

- Scrapes a product page once per day
- Compares price to the previous day
- Sends a Telegram message on price change (with history)
- Retries hourly on network/parse failure
- Uses systemd user timers for scheduling
- No external Python dependencies

## Requirements

- Python 3.7+
- Ubuntu/Debian Linux with systemd
- Telegram Bot Token and Chat ID

## Quick Start

### 1. Get Telegram Credentials

1. Open Telegram and talk to [@BotFather](https://t.me/BotFather)
2. Run `/newbot`, choose a name and username, and copy the bot token
3. Open your new bot chat and send any message (e.g., "hi")
4. Open in browser: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find your message and copy the `chat.id`

### 2. Clone and Run Setup

```bash
git clone https://github.com/zcamak/media_expert_samsung_tv_check.git
cd media_expert_samsung_tv_check/
./setup.sh
```

The script will:
- Create a Python virtual environment
- Generate a `.env` file template
- Copy systemd unit files
- Print next steps

### 3. (Manual) Add Credentials

Edit `.env` and fill in your token and chat ID:

```
TELEGRAM_BOT_TOKEN=your_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id_from_getUpdates
```

### 4. Test

```bash
./.venv/bin/python execution/price_watch.py --force-notify
```

You should receive a Telegram message.

### 5. Enable the Timer

```bash
systemctl --user enable --now price-watch.timer
systemctl --user list-timers
```

The timer runs daily at 08:00 UTC. If it fails, it retries hourly until success.

## Usage

### Manual Run

Test without sending notification:
```bash
./.venv/bin/python execution/price_watch.py
```

Force notification (for testing):
```bash
./.venv/bin/python execution/price_watch.py --force-notify
```

### Manage Timer

List all timers:
```bash
systemctl --user list-timers
```

Disable timer (stop checking):
```bash
systemctl --user disable --now price-watch.timer
```

Re-enable timer:
```bash
systemctl --user enable --now price-watch.timer
```

View logs:
```bash
journalctl --user -u price-watch.service --since today
```

## Configuration

Edit the product URL in `execution/price_watch.py`:

```python
DEFAULT_URL = "https://example.com/product"
```

Change the daily schedule in `systemd/price-watch.timer`:

```ini
[Timer]
OnCalendar=*-*-* 08:00:00  # Change 08:00 to your preferred time
```

Then reload systemd:

```bash
systemctl --user daemon-reload
systemctl --user restart price-watch.timer
```

## Architecture

- **execution/price_watch.py** — Main script: fetches page, parses price, sends notifications
- **directives/price_watch.md** — SOP and design notes
- **SETUP.md** — Manual setup instructions
- **systemd/** — Unit files for systemd user service and timer
- **.env** — Telegram credentials (keep private)
- **.tmp/price_history.json** — Local price history (auto-generated, ignored in git)

## Troubleshooting

**Script fails with 403 Forbidden**
- The website may be blocking your user-agent. The script sends realistic browser headers; if it still fails, check if the URL is correct and accessible.

**Telegram message not received**
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Check logs: `journalctl --user -u price-watch.service --since today`

**Timer not firing**
- Ensure user session is running: `systemctl --user status`
- Check timer status: `systemctl --user list-timers`
- View logs: `journalctl --user -u price-watch.service`

## License

MIT

## Attribution

The 3-layer architecture (AGENTS.md) is based on [Nick Saraev's](https://www.youtube.com/@nicksaraev) approach to reliable agent systems with deterministic execution layers.
