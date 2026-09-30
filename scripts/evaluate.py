#!/usr/bin/env python3
"""Read-only, secret-safe profile checks. Never print subprocess output or config."""
import argparse
import grp
import json
import os
import platform
import pwd
import re
import subprocess
import sys
from pathlib import Path

# Do not inherit cloud credentials, Docker remote contexts, Python hooks or user PATH.
ENV = {
    'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    'LANG': 'C',
    'LC_ALL': 'C',
    'HOME': '/var/empty',
    'DOCKER_HOST': 'unix:///var/run/docker.sock',
}


def result(name, passed):
    return {'name': name, 'status': 'pass' if passed else 'fail'}


def run(argv):
    return subprocess.run(argv, capture_output=True, text=True, timeout=20, env=ENV, check=False)


def probe(name, argv):
    try:
        return result(name, run(argv).returncode == 0)
    except (OSError, subprocess.TimeoutExpired):
        return result(name, False)


def server_gui_check():
    """Desktop payloads are failures; libraries and removed package records are not."""
    try:
        completed = run(['dpkg-query', '-W', '-f=${Package}\t${db:Status-Status}\n'])
        if completed.returncode:
            return result('server_without_desktop', False)
        forbidden = re.compile(r'^(ubuntu-desktop.*|kubuntu-desktop|xubuntu-desktop|'
                               r'lubuntu-desktop|ubuntu-mate-desktop|gnome-shell|'
                               r'plasma-desktop|xfce4|hyprland|xserver-xorg|'
                               r'code|cursor|discord|spotify-client|hyper)$')
        installed = [line.split('\t', 1)[0] for line in completed.stdout.splitlines()
                     if line.endswith('\tinstalled')]
        return result('server_without_desktop', not any(forbidden.match(p) for p in installed))
    except (OSError, subprocess.TimeoutExpired):
        return result('server_without_desktop', False)


def package_check(profile, package):
    if profile == 'ubuntu_server':
        try:
            completed = run(['dpkg-query', '-W', '-f=${db:Status-Status}', package])
            return result('package:' + package, completed.returncode == 0 and completed.stdout == 'installed')
        except (OSError, subprocess.TimeoutExpired):
            return result('package:' + package, False)
    if profile == 'omarchy_desktop':
        return probe('package:' + package, ['pacman', '-Q', package])
    # Listing installed Homebrew metadata can refresh caches. Check the cellar instead.
    return result('package:' + package, any((Path(root) / package).is_dir()
                  for root in ['/opt/homebrew/Cellar', '/usr/local/Cellar']))


SLEEP_OPTIONS = ['AllowSuspend', 'AllowHibernation', 'AllowHybridSleep', 'AllowSuspendThenHibernate']
LOGIN_OPTIONS = ['IdleAction', 'HandleSuspendKey', 'HandleSuspendKeyLongPress',
                 'HandleHibernateKey', 'HandleHibernateKeyLongPress', 'HandleLidSwitch',
                 'HandleLidSwitchExternalPower', 'HandleLidSwitchDocked']


def config_values(text, section):
    values = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', ';')):
            continue
        if line.startswith('[') and line.endswith(']'):
            current = line[1:-1]
        elif current == section and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
    return values


def always_on_checks(services):
    checks = []
    for name, section, options, expected in [('sleep', 'Sleep', SLEEP_OPTIONS, 'no'),
                                              ('logind', 'Login', LOGIN_OPTIONS, 'ignore')]:
        try:
            completed = run(['systemd-analyze', 'cat-config', 'systemd/' + name + '.conf'])
            values = config_values(completed.stdout, section)
            checks.append(result('always_on_effective_' + name,
                                 completed.returncode == 0 and all(values.get(k) == expected for k in options)))
        except (OSError, subprocess.TimeoutExpired):
            checks.append(result('always_on_effective_' + name, False))
    if services:
        # Read-only capability queries: never attempt to suspend the test machine.
        for method in ['CanSuspend', 'CanHibernate', 'CanHybridSleep', 'CanSuspendThenHibernate']:
            try:
                completed = run(['busctl', 'call', 'org.freedesktop.login1', '/org/freedesktop/login1',
                                 'org.freedesktop.login1.Manager', method])
                checks.append(result('logind_' + method,
                                     completed.returncode == 0 and completed.stdout.strip() in ['s "na"', 's "no"']))
            except (OSError, subprocess.TimeoutExpired):
                checks.append(result('logind_' + method, False))
        for option in LOGIN_OPTIONS:
            try:
                completed = run(['busctl', 'get-property', 'org.freedesktop.login1', '/org/freedesktop/login1',
                                 'org.freedesktop.login1.Manager', option])
                checks.append(result('logind_live_' + option,
                                     completed.returncode == 0 and completed.stdout.strip() == 's "ignore"'))
            except (OSError, subprocess.TimeoutExpired):
                checks.append(result('logind_live_' + option, False))
    else:
        checks.append({'name': 'always_on_live_logind', 'status': 'skip'})
    return checks


def tailscale_checks():
    checks = []
    try:
        completed = run(['tailscale', 'version'])
        first = completed.stdout.splitlines()[0] if completed.stdout else ''
        valid = completed.returncode == 0 and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', first) is not None
        check = result('tailscale_version', valid)
        if valid:
            check['version'] = first
        checks.append(check)
        installed = run(['pacman', '-Q', 'tailscale'])
        available = run(['pacman', '-Si', 'extra/tailscale'])
        metadata = dict((k.strip(), v.strip()) for line in available.stdout.splitlines()
                        if ':' in line for k, v in [line.split(':', 1)])
        parts = installed.stdout.split()
        checks.append(result('tailscale_latest_stable_repository',
                             installed.returncode == available.returncode == 0 and len(parts) == 2
                             and metadata.get('Repository') == 'extra' and parts[1] == metadata.get('Version')))
    except (OSError, subprocess.TimeoutExpired):
        checks.append(result('tailscale_installation', False))
    # Authentication is deliberately separate; no auth state, peer list or keys are read.
    checks.append({'name': 'tailscale_tailnet_authentication', 'status': 'skip'})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, choices=['ubuntu_server', 'omarchy_desktop', 'macos'])
    parser.add_argument('--home', required=True, type=Path)
    parser.add_argument('--command', action='append', default=[])
    parser.add_argument('--package', action='append', default=[])
    parser.add_argument('--always-on', action='store_true')
    parser.add_argument('--docker', action='store_true')
    parser.add_argument('--services', action='store_true')
    parser.add_argument('--docker-runtime', action='store_true')
    parser.add_argument('--docker-group-user')
    args = parser.parse_args()
    checks = [result('target_home', args.home.is_dir())]
    if args.profile == 'macos':
        checks.append(result('platform', platform.system() == 'Darwin'))
    else:
        try:
            release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
            distro = release.get('ID', '').strip('"')
        except OSError:
            distro = ''
        checks.append(result('platform', distro == ('ubuntu' if args.profile == 'ubuntu_server' else 'arch')))
    # command -v is a shell builtin; fixed positional arguments avoid shell injection.
    for binary in args.command:
        checks.append(probe('command:' + binary, ['sh', '-c', 'command -v "$1" >/dev/null', 'check', binary]))
    for package in args.package:
        checks.append(package_check(args.profile, package))
    if args.profile == 'ubuntu_server':
        checks.append(server_gui_check())
    if args.profile == 'omarchy_desktop':
        checks.append(result('omarchy_installation', any(p.is_file() for p in [
            args.home / '.local/share/omarchy/bin/omarchy-version', Path('/usr/share/omarchy/bin/omarchy-version')])))
    if args.docker:
        checks.append(probe('docker_client', ['docker', '--version']))
        checks.append(probe('docker_compose_plugin', ['docker', 'compose', 'version']))
        if args.profile != 'macos':
            checks.append(probe('docker_buildx_plugin', ['docker', 'buildx', 'version']))
        if args.profile == 'macos':
            if args.docker_runtime:
                # Explicit Colima check, never connect to an inherited cloud Docker context.
                ENV['HOME'] = str(args.home)
                checks.append(probe('colima_runtime', ['colima', 'status']))
            else:
                checks.append({'name': 'colima_runtime', 'status': 'skip'})
        elif args.services:
            checks.append(probe('docker_runtime', ['docker', 'info', '--format', '{{.ServerVersion}}']))
        else:
            checks.append({'name': 'docker_runtime', 'status': 'skip'})
    if args.services and args.profile != 'macos':
        services = ['ssh'] if args.profile == 'ubuntu_server' else []
        if args.docker:
            services.append('docker')
        if args.profile == 'omarchy_desktop':
            services.append('tailscaled')
        for service in services:
            checks.append(probe('service_active:' + service, ['systemctl', 'is-active', '--quiet', service]))
            checks.append(probe('service_enabled:' + service, ['systemctl', 'is-enabled', '--quiet', service]))
    else:
        checks.append({'name': 'system_services', 'status': 'skip'})
    if args.docker_group_user:
        try:
            account = pwd.getpwnam(args.docker_group_user)
            group = grp.getgrnam('docker')
            member = group.gr_gid in os.getgrouplist(account.pw_name, account.pw_gid)
        except KeyError:
            member = False
        checks.append(result('docker_group_membership', member))
    if args.profile == 'omarchy_desktop':
        checks.extend(tailscale_checks())
    if args.always_on:
        checks.extend(always_on_checks(args.services))
    print(json.dumps({'profile': args.profile, 'checks': checks}, sort_keys=True))
    return int(any(check['status'] == 'fail' for check in checks))


if __name__ == '__main__':
    sys.exit(main())
