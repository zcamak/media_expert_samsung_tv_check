# Price Watcher (MediaExpert)

## Goal
Check the product price once per day, compare to last recorded value, and send a Telegram message when the price changes (or when forced for testing).

## Inputs
- Product URL
- Telegram bot token and chat ID
- Optional CLI flags (force notify, timeout, custom history path)

## Tools/Scripts
- execution/price_watch.py (main script)

## Outputs
- Local history file in .tmp/price_history.json
- Telegram messages for price changes (or forced notifications)

## Data Storage
- Append-only entries when the price changes:
  - date: YYYY-MM-DD (local time)
  - price: string normalized with dot decimal (e.g., 7799.00)
  - currency: e.g., PLN

## Environment Variables
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

## Edge Cases
- First run: no prior history, store current price; notify only if force flag is set.
- Parse failure: exit non-zero so systemd restarts the service after 1 hour.
- Network failure/timeouts: exit non-zero so systemd restarts the service after 1 hour.
- Price unchanged: do nothing (unless force flag).

## Systemd Scheduling (Ubuntu 24.04)
- Use a daily timer to start the service.
- Service uses Restart=on-failure and RestartSec=1h to retry hourly until success.

### Sample unit files
Create these under ~/.config/systemd/user/ and adjust paths if needed.

price-watch.service

[Unit]
Description=Daily price watch

[Service]
Type=oneshot
WorkingDirectory=%h/mytools/samsung_tv
EnvironmentFile=%h/mytools/samsung_tv/.env
ExecStart=%h/mytools/samsung_tv/.venv/bin/python %h/mytools/samsung_tv/execution/price_watch.py
Restart=on-failure
RestartSec=1h

[Install]
WantedBy=default.target

price-watch.timer

[Unit]
Description=Run price watch daily

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true
Unit=price-watch.service

[Install]
WantedBy=timers.target

### Enable the timer
systemctl --user daemon-reload
systemctl --user enable --now price-watch.timer
systemctl --user list-timers --all | grep price-watch

## Runbook
1. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env or environment.
2. Run:
   python3 execution/price_watch.py --force-notify
3. Verify a Telegram message is received.
4. Enable systemd timer/service for daily checks.
