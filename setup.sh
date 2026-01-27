#!/bin/bash
set -e

# Ansible Workbench Setup Script

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Ansible Workbench Setup...${NC}"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# 2. Check for pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip3 not found, attempting to install...${NC}"
    if [ -f /etc/debian_version ]; then
        sudo apt update && sudo apt install -y python3-pip
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S --noconfirm python-pip
    elif [ -f /etc/fedora-release ]; then
        sudo dnf install -y python3-pip
    else
        echo -e "${RED}Could not install pip3 automatically. Please install it manually.${NC}"
        exit 1
    fi
fi

# 3. Check for Ansible
if ! command -v ansible-playbook &> /dev/null; then
    echo -e "${YELLOW}Ansible not found. Installing Ansible...${NC}"
    # Check if we should use a venv or install globally. 
    # For simplicity in this user script, let's try to use pip3 user install or global if user prefers.
    # We will assume a user install to avoid breaking system packages.
    pip3 install --user ansible
    
    # Add user bin to PATH if not there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}Adding $HOME/.local/bin to PATH temporarily...${NC}"
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    if ! command -v ansible-playbook &> /dev/null; then
         echo -e "${RED}Ansible installation failed or not in PATH. Please install Ansible manually.${NC}"
         exit 1
    fi
else
    echo -e "${GREEN}Ansible is already installed.${NC}"
fi

# 4. Run Playbook
echo -e "${GREEN}Running Ansible Playbook...${NC}"
# Prompt for sudo password if needed by ansible (using -K)
# We can check if -K is needed or just ask the user. 
# Usually for system setups sudo is required.
echo -e "${YELLOW}Note: You may be asked for your sudo password for package installations.${NC}"

read -p "Do you want to run the playbook now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ansible-playbook site.yml -K
else
    echo -e "${YELLOW}Skipping playbook execution.${NC}"
fi

echo -e "${GREEN}Setup script finished.${NC}"
