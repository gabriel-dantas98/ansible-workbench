# How to Use Ansible Workbench

This repository contains an Ansible playbook to automate the setup of a development environment.

## Prerequisites

- **Operating System**: Linux (Ubuntu/Debian based recommended, or Arch/Fedora as supported by roles)
- **Python**: Python 3 must be installed.
- **Git**: To clone this repository.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gabriel-dantas98/ansible-workbench.git
   cd ansible-workbench
   ```

2. **Run the setup script:**
   We provide a `setup.sh` script to check for dependencies (Ansible) and install them if missing, then run the playbook.
   ```bash
   ./setup.sh
   ```

   **Alternatively, manual execution:**
   If you have Ansible installed:
   ```bash
   ansible-playbook site.yml
   ```
   *Note: You might need `-K` to ask for sudo password if required tasks need privilege escalation.*

## Roles Overview

- **base**: System updates and essential packages (curl, wget, git, etc.).
- **shell**: Zsh configuration, Oh-My-Zsh, plugins.
- **version_managers**: asdf / rtx / nvm setup.
- **containerization**: Docker / Podman setup.
- **cloud_k8s**: Kubernetes tools (kubectl, k9s, helm) and Cloud CLI tools (AWS, GCP, Azure).
- **languages**: Programming language runtimes (Go, Rust, Node.js, Python).
- **editors**: VS Code / Neovim configuration.

## Customization

Modify `inventory.ini` or `group_vars` (if present) to customize the installation target, though it defaults to `localhost`.
Edit specific roles in `roles/` to add or remove packages.
