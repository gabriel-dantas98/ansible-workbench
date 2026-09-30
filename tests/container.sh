#!/usr/bin/env bash
set -euo pipefail
# Runs on disposable CI runners. Explicit opt-in for local use; never starts Colima.
if [[ ${CI:-} != true && ${WORKBENCH_ALLOW_CONTAINER_TESTS:-} != yes ]]; then
  echo 'Container tests require CI=true or WORKBENCH_ALLOW_CONTAINER_TESTS=yes.' >&2
  exit 2
fi
case ${1:-} in
  ubuntu24) image=ubuntu:24.04; profile=ubuntu_server ;;
  ubuntu26) image=ubuntu:26.04; profile=ubuntu_server ;;
  arch) image=archlinux:base; profile=omarchy_desktop ;;
  *) echo 'Usage: tests/container.sh ubuntu24|ubuntu26|arch' >&2; exit 2 ;;
esac
# No privileged mode, host mounts, host networking or Docker socket mounts.
docker info >/dev/null
free_kb=$(df -Pk . | awk 'NR==2 {print $4}')
if (( free_kb < 6 * 1024 * 1024 )); then
  echo 'Need at least 6 GiB free before pulling/building test images.' >&2
  exit 1
fi
container="workbench-${1}-$$"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true' EXIT
docker run --name "$container" --detach "$image" sleep infinity >/dev/null
if [[ $profile == ubuntu_server ]]; then
  docker exec "$container" sh -c 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-apt sudo systemd ca-certificates'
else
  # This is an Arch package fixture, NOT an Omarchy desktop/hardware test.
  docker exec "$container" sh -c 'pacman -Syu --noconfirm --needed python sudo git jq ripgrep tmux neovim mise docker docker-compose docker-buildx'
  docker exec "$container" sh -c 'mkdir -p /usr/share/omarchy/bin; printf "fixture only\n" > /usr/share/omarchy/bin/omarchy-version'
fi
docker exec "$container" useradd -m -s /bin/bash homelabtest
# Preserve representative user files byte-for-byte through both applies.
docker exec "$container" sh -c 'printf "preserve shell\n" > /home/homelabtest/.bashrc; mkdir -p /home/homelabtest/.config/hypr; printf "lock and DPMS fixture\n" > /home/homelabtest/.config/hypr/hypridle.conf'
mkdir -p artifacts
cat > artifacts/inventory.yml <<EOF_INVENTORY
all:
  children:
    workbench:
      hosts:
        $container:
          ansible_connection: community.docker.docker
          ansible_python_interpreter: /usr/bin/python3
          workbench_user: homelabtest
          workbench_profile: $profile
          workbench_manage_services: false
          workbench_docker_group: true
EOF_INVENTORY
export ANSIBLE_NOCOLOR=1
ansible-playbook -i artifacts/inventory.yml site.yml --check | tee artifacts/check-before.log
ansible-playbook -i artifacts/inventory.yml site.yml | tee artifacts/apply.log
ansible-playbook -i artifacts/inventory.yml site.yml | tee artifacts/idempotence.log
grep -Eq 'changed=0 .*failed=0' artifacts/idempotence.log
ansible-playbook -i artifacts/inventory.yml site.yml --check | tee artifacts/check-after.log
grep -Eq 'changed=0 .*failed=0' artifacts/check-after.log
ansible-playbook -i artifacts/inventory.yml validate.yml | tee artifacts/evaluation.log
if [[ $profile == omarchy_desktop ]]; then
  # Exercise the real daemon without a TUN device, host privileges or tailnet auth.
  docker cp scripts/evaluate.py "$container":/tmp/workbench-evaluate.py
  docker exec --detach "$container" tailscaled --tun=userspace-networking --state=mem: --socket=/tmp/workbench-tailscaled.sock
  for _attempt in {1..20}; do
    if docker exec "$container" test -S /tmp/workbench-tailscaled.sock; then break; fi
    sleep 1
  done
  docker exec "$container" python3 -c 'import json,subprocess; p=subprocess.run(["tailscale","--socket=/tmp/workbench-tailscaled.sock","status","--json"],capture_output=True,text=True); s=json.loads(p.stdout); assert s["BackendState"] == "NeedsLogin"; print("Tailscale daemon operational; authentication pending")'
  docker exec "$container" python3 -c 'import runpy; m=runpy.run_path("/tmp/workbench-evaluate.py"); check=m["tailscale_daemon_check"]("/tmp/workbench-tailscaled.sock"); print(check); assert check["status"] == "pass"'
fi
# Power policy must be reversible, and disabling it must not rewrite desktop files.
ansible-playbook -i artifacts/inventory.yml site.yml -e '{"workbench_always_on": false}' | tee artifacts/power-disable.log
docker exec "$container" sh -c 'test ! -e /etc/systemd/sleep.conf.d/90-ansible-workbench.conf && test ! -e /etc/systemd/logind.conf.d/90-ansible-workbench.conf'
ansible-playbook -i artifacts/inventory.yml site.yml | tee artifacts/power-restore.log
docker exec "$container" sh -c 'test "$(cat /home/homelabtest/.bashrc)" = "preserve shell"; test "$(cat /home/homelabtest/.config/hypr/hypridle.conf)" = "lock and DPMS fixture"'
# A later override must be detected, not hidden by the existence of our file.
docker exec "$container" sh -c 'printf "[Sleep]\nAllowSuspend=yes\n" > /etc/systemd/sleep.conf.d/99-drift.conf'
if ansible-playbook -i artifacts/inventory.yml validate.yml > artifacts/expected-power-drift.log 2>&1; then
  echo 'ERROR: evaluator accepted overridden always-on policy' >&2; exit 1
fi
grep -q 'always_on_effective_sleep' artifacts/expected-power-drift.log
docker exec "$container" rm /etc/systemd/sleep.conf.d/99-drift.conf
# A missing managed executable/package must also fail validation.
docker exec "$container" rm /usr/bin/shellcheck
if ansible-playbook -i artifacts/inventory.yml validate.yml > artifacts/expected-tool-drift.log 2>&1; then
  echo 'ERROR: evaluator accepted missing shellcheck' >&2; exit 1
fi
grep -q 'command:shellcheck' artifacts/expected-tool-drift.log
# The wrong OS/profile fails before any installation task.
if ansible-playbook -i artifacts/inventory.yml site.yml -e workbench_profile=macos > artifacts/expected-profile-rejection.log 2>&1; then
  echo 'ERROR: incompatible profile was accepted' >&2; exit 1
fi
grep -q 'Reject incompatible operating systems' artifacts/expected-profile-rejection.log
