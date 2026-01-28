# Ansible Workbench

Automate your development environment setup with Ansible. This playbook sets up a comprehensive workbench including shell configurations, version managers, container tools, Kubernetes utilities, programming languages, and editors.

## Prerequisites

- **Operating System**: Linux (Ubuntu/Debian, Arch, Fedora supported)
- **Python**: Python 3 must be installed.
- **Git**: Required to clone the repository.

## Installation

1. **Get the code:**

   **Option A: Clone with Git (Recommended)**
   ```bash
   git clone https://github.com/gabriel-dantas98/ansible-workbench.git
   cd ansible-workbench
   ```

   **Option B: Download without Git**
   
   If you don't have git installed yet, run this one-liner to download and extract the latest version:
   ```bash
   curl -L https://github.com/gabriel-dantas98/ansible-workbench/archive/master.tar.gz | tar xz
   cd ansible-workbench-master
   ```

2. **Run the setup script:**

   We provide a helper script to check dependencies and run the playbook:

   ```bash
   ./setup.sh
   ```

   Alternatively, you can run Ansible directly if installed:

   ```bash
   ansible-playbook site.yml --ask-become-pass
   ```

## Roles Included

- **base**: Essential system packages (curl, wget, build-essential).
- **shell**: Zsh, Oh-My-Zsh, and plugins.
- **version_managers**: asdf / rtx for managing tool versions.
- **containerization**: Docker and Podman.
- **cloud_k8s**: kubectl, k9s, helm, AWS CLI, Google Cloud SDK.
- **languages**: Go, Rust, Node.js, Python environment.
- **editors**: VS Code and Neovim configurations.

## Customization

- **Inventory**: Modify `inventory.ini` to change target hosts (default: `localhost`).
- **Variables**: adjust `group_vars/all.yml` or role-specific variables in `roles/<role>/defaults/main.yml`.

## Verification

To verify your installation, you can run the following commands:

- **Shell**: `zsh --version`
- **Docker**: `docker --version`
- **Kubernetes**: `kubectl version --client` and `k9s version`
- **Languages**: 
  - Go: `go version`
  - Node: `node --version` (requires new terminal or `source ~/.zshrc`)
  - Python: `python3 --version` (via pyenv)
- **Tools**:
  - Discord: `discord --version`
  - Spotify: `spotify --version`
  - VS Code: `code --version`
