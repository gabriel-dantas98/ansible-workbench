#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ $(uname -s) == Linux && $EUID -ne 0 ]] || { echo 'Run as the target Linux user, without sudo.' >&2; exit 1; }
command -v git >/dev/null
command -v uv >/dev/null
revision=f97608f178d1ffeca59860195ab7da295f7c8e5f
release=v2026.9.24
install_dir="$HOME/.hermes/hermes-agent"
wrapper="$HOME/.local/bin/hermes-homelab"
write_launcher() {
  cat <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
exec "$HOME/.hermes/hermes-agent/venv/bin/hermes" "$@"
WRAPPER
}
if [[ -L "$wrapper" ]] || { [[ -e "$wrapper" ]] && ! cmp -s "$wrapper" <(write_launcher); }; then
  echo 'Existing hermes-homelab is not our launcher; stopped.' >&2
  exit 1
fi
mkdir -p "$HOME/.hermes"
if [[ ! -d "$install_dir/.git" ]]; then
  git clone --depth 1 --branch "$release" https://github.com/NousResearch/hermes-agent.git "$install_dir"
fi
[[ "$(git -C "$install_dir" rev-parse HEAD)" == "$revision" ]] || { echo 'Unexpected Hermes revision; stopped.' >&2; exit 1; }
git -C "$install_dir" diff --quiet HEAD -- || { echo 'Modified Hermes checkout; stopped.' >&2; exit 1; }
cd "$install_dir"
UV_PROJECT_ENVIRONMENT="$install_dir/venv" uv sync --python 3.13 --extra all --locked --no-dev
"$install_dir/venv/bin/hermes" --version
mkdir -p "$HOME/.local/bin"
write_launcher > "$wrapper"
chmod 700 "$wrapper"
if [[ ! -e "$HOME/.hermes/.env" ]]; then
  printf '%s\n' '# Provider authentication pending; no credentials copied.' > "$HOME/.hermes/.env"
fi
if [[ ! -e "$HOME/.hermes/config.yaml" ]]; then
  printf '%s\n' '_config_version: 46' 'display:' '  interface: cli' > "$HOME/.hermes/config.yaml"
fi
uv pip check --python "$install_dir/venv/bin/python"
