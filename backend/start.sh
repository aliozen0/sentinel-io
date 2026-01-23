#!/bin/bash
set -e

# --- SSH Setup ---
echo "🔑 Generating SSH Keys if missing..."

mkdir -p /app/keys
KEYS_DIR="/app/keys"
PRIVATE_KEY="$KEYS_DIR/demo_id_rsa"
PUBLIC_KEY="$PRIVATE_KEY.pub"

if [ ! -f "$PRIVATE_KEY" ]; then
    # Generate new key pair (no passphrase for demo simplicity)
    ssh-keygen -t rsa -b 2048 -f "$PRIVATE_KEY" -N "" -q
    echo "✅ Generated new demo keys."
else
    echo "♻️  Using existing demo keys."
fi

# Ensure correct permissions
chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

# Setup SSH for root (or a specific user if we switched)
# For this demo/simulation, we'll allow root login with key
mkdir -p /root/.ssh
cat "$PUBLIC_KEY" > /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

# Configure SSHD
mkdir -p /run/sshd
# Ensure host keys are generated (sometimes missing in containers)
ssh-keygen -A

# Allow root login, disable password auth (force key), etc.
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
# Disable PAM to avoid authentication issues in some containers
echo "UsePAM no" >> /etc/ssh/sshd_config

echo "🚀 Starting SSH Daemon..."
/usr/sbin/sshd

# --- App Application ---
echo "🔥 Starting io-Guard Backend..."

# Forward arguments to CMD (uvicorn)
exec "$@"
