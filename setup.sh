#!/usr/bin/env bash
set -euo pipefail
# Deliberately does not install anything on the controller.
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 INVENTORY HOST [ansible-playbook options]" >&2
  exit 2
fi
inventory=$1
host=$2
shift 2
command -v ansible-playbook >/dev/null || { echo "Install Ansible on your controller first." >&2; exit 1; }
cd "$(dirname "$0")"
exec ansible-playbook -i "$inventory" site.yml --limit "$host" "$@"
