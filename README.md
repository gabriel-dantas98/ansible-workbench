# Ansible Workbench

Automate your development environment setup with Ansible. This playbook sets up a comprehensive workbench including shell configurations, version managers, container tools, Kubernetes utilities, programming languages, and editors.

## Prerequisites

- **Operating System**: Linux (Ubuntu/Debian, Arch, Fedora supported)
- **Python**: Python 3 must be installed.
- **Git**: Required to clone the repository.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gabriel-dantas98/ansible-workbench.git
   cd ansible-workbench
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
