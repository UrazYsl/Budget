#!/usr/bin/env bash
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# ── Docker install (Ubuntu/Debian only, skipped if already present) ──
if ! command -v docker &>/dev/null; then
    echo "Docker not found. Installing..."
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose-v2
    sudo usermod -aG docker "$USER"
    echo ""
    echo "Docker installed. You may need to log out and back in for group changes to take effect."
    echo "If the next step fails with a permission error, run: newgrp docker"
    echo ""
fi

# ── Ensure Docker daemon starts on boot ──
if ! sudo systemctl is-enabled docker &>/dev/null; then
    echo "Enabling Docker daemon to start on boot..."
    sudo systemctl enable docker
fi

# ── Avahi (local hostname, e.g. http://budget.local) ──
if ! command -v avahi-daemon &>/dev/null; then
    echo "Installing avahi-daemon for local hostname access..."
    sudo apt-get update -y
    sudo apt-get install -y avahi-daemon
    sudo systemctl enable --now avahi-daemon
fi

# ── Tailscale (remote access, skipped if already installed) ──
if ! command -v tailscale &>/dev/null; then
    echo "Installing Tailscale for remote access..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo ""
    echo "Tailscale installed. To enable remote access, run once:"
    echo "  sudo tailscale up"
    echo "Then install the Tailscale app on your phone/laptop and sign in with the same account."
    echo ""
fi

# ── .env ──
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "Created .env from .env.example. Edit it to set your password and timezone."
fi

# ── Hostname (read from .env, default: budget) ──
APP_HOSTNAME=$(grep -E '^APP_HOSTNAME=' "$SCRIPT_DIR/.env" 2>/dev/null | cut -d'=' -f2 | tr -d '[:space:]"')
APP_HOSTNAME=${APP_HOSTNAME:-budget}
if [ "$(hostname)" != "$APP_HOSTNAME" ]; then
    echo "Setting hostname to '$APP_HOSTNAME'..."
    sudo hostnamectl set-hostname "$APP_HOSTNAME"
fi

# ── Port 80 conflict check ──
if ss -tlnp 2>/dev/null | grep -q ':80 '; then
    if ! docker ps --format '{{.Ports}}' 2>/dev/null | grep -q '0.0.0.0:80->'; then
        echo "WARNING: Port 80 is already in use by a non-Docker process."
        echo "  → Stop it first, or change '80:80' to e.g. '8080:80' in docker-compose.yml."
        echo ""
    fi
fi

# ── Start ──
cd "$SCRIPT_DIR"
docker compose up -d --build

# ── Schedule daily backup at 2 AM (skipped if already registered) ──
CRON_CMD="0 2 * * * bash \"$SCRIPT_DIR/backup.sh\" >> \"$HOME/budget-backups/backup.log\" 2>&1"
if ! crontab -l 2>/dev/null | grep -qF "$SCRIPT_DIR/backup.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Daily backup scheduled at 2 AM → $HOME/budget-backups/"
fi

echo ""
echo "App is running at:"
echo "  http://localhost              (on this machine)"
echo "  http://${APP_HOSTNAME}.local  (from any device on the network)"
echo ""
echo "API docs: http://localhost/api/docs"
