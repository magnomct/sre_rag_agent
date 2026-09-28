#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing GitHub CLI ==="

curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null

sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg

ARCH=$(dpkg --print-architecture)
echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

sudo apt-get update -qq
sudo apt-get install -y gh

echo ""
gh --version
echo "=== Done ==="
