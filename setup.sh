#!/usr/bin/env bash
set -euo pipefail

echo "=== Price Watcher Setup ==="
echo

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
ENV_FILE="$PROJECT_ROOT/.env"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "Project root: $PROJECT_ROOT"
echo "Systemd files will be installed to: $SYSTEMD_USER_DIR"
echo

# Check if .venv exists
if [[ -d "$VENV_PATH" ]]; then
    echo "✓ Virtual environment already exists."
else
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_PATH"
    echo "✓ Virtual environment created."
fi

# Check if .env exists
if [[ -f "$ENV_FILE" ]]; then
    echo "✓ .env file exists (keeping existing credentials)."
else
    echo "Creating .env template..."
    cat > "$ENV_FILE" <<'ENVFILE'
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ENVFILE
    echo "✓ .env created. Edit it with your Telegram credentials."
    echo "  See README.md for how to obtain bot token and chat ID."
    echo
fi

# Setup systemd directories
echo "Setting up systemd user service files..."
mkdir -p "$SYSTEMD_USER_DIR"

# Copy unit files (they use %h placeholder which systemd expands)
cp "$PROJECT_ROOT/systemd/price-watch.service" "$SYSTEMD_USER_DIR/"
cp "$PROJECT_ROOT/systemd/price-watch.timer" "$SYSTEMD_USER_DIR/"
echo "✓ Copied unit files to $SYSTEMD_USER_DIR/"

echo

read -p "Enable the timer now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl --user daemon-reload
    systemctl --user enable --now price-watch.timer
    echo "✓ Timer enabled and started."
    echo
    systemctl --user list-timers --all | grep price-watch || true
else
    echo "Skipped. To enable later, run:"
    echo "  systemctl --user daemon-reload"
    echo "  systemctl --user enable --now price-watch.timer"
fi

echo
echo "=== Next Steps ==="
echo
echo "1. Edit .env with your Telegram credentials:"
echo "   nano $ENV_FILE"
echo
echo "2. Test the script:"
echo "   $VENV_PATH/bin/python execution/price_watch.py --force-notify"
echo
echo "3. If you haven't enabled the timer yet, run:"
echo "   systemctl --user enable --now price-watch.timer"
echo
echo "4. Check timer status:"
echo "   systemctl --user list-timers"
echo
echo "See README.md for more details."
