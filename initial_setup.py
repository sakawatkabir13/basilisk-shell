#!/usr/bin/env python3
import subprocess
import sys
import os

python_packages = ["groq", "python-dotenv"]
scripts_to_make_executable = ["basilisk.sh", "run.sh"]

# theme Colours
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
MINT = "\033[38;5;121m"
GREY = "\033[90m"
WHITE = "\033[97m"
DIM = "\033[2m"

def install_system_packages():
    print(f"{YELLOW + BOLD}Installing required system packages...{RESET}")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        print(f"{MINT + BOLD}System packages installed successfully!{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}Failed to install system packages. Make sure you're using a Debian-based system with sudo access.")

def setup_virtualenv():
    print(f"{YELLOW + BOLD}Setting up Python virtual environment...{RESET}")
    if not os.path.exists("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print(f"{MINT + BOLD}Virtual environment created.{RESET}")
    else:
        print(f"{GREEN + BOLD}Virtual environment already exists.{RESET}")

def install_python_packages():
    print(f"{YELLOW + BOLD}Installing Python packages inside virtual environment...{RESET}")
    try:
        subprocess.run(["venv/bin/python", "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(["venv/bin/python", "-m", "pip", "install"] + python_packages, check=True)
        print(f"{MINT + BOLD}Python packages installed successfully!{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}Failed to install Python packages.{RESET}")

def create_run_script():
    print(f"{YELLOW + BOLD}Creating run.sh to auto-activate venv and launch the tool...{RESET}")
    script_content = """#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"

msg="Starting the Powerful AI-Powered Basilisk Shell....."
for (( i=0; i<${#msg}; i++ )); do
    echo -n "${msg:$i:1}"
    sleep 0.03
done
echo

python3 "$SCRIPT_DIR/basilisk_ai_setup.py"
"""
    with open("run.sh", "w") as f:
        f.write(script_content)
    print(f"{MINT + BOLD}run.sh created successfully!{RESET}")

def create_symlink():
    print(f"{YELLOW + BOLD}Creating global {RED}`basilisk`{RESET} symlink...{RESET}")
    symlink_target1 = os.path.join(os.getcwd(), "basilisk.sh")
    symlink_path = "/usr/local/bin/basilisk"
    try:
        if os.path.exists(symlink_path) or os.path.islink(symlink_path):
            subprocess.run(["sudo", "rm", "-f", symlink_path], check=True)
        subprocess.run(["sudo", "ln", "-s", symlink_target1, symlink_path], check=True)
        print(f"{MINT + BOLD}Symlink created successfully!{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}Failed to create symlink. Make sure you have sudo access.{RESET}")

def make_scripts_executable():
    print(f"{YELLOW + BOLD}Setting executable permissions...{RESET}")
    for script in scripts_to_make_executable:
        if os.path.exists(script):
            try:
                subprocess.run(["chmod", "+x", script], check=True)
                print(f"{GREEN}{script} is now executable.{RESET}")
            except subprocess.CalledProcessError:
                print(f"{RED}Failed to set permission for {script}.{RESET}")
        else:
            print(f"{RED}Script not found: {script}{RESET}")

def print_final_message():
    print(f"{CYAN + BOLD}Setup completed successfully!\n{RESET}")
    print(f"{CYAN + BOLD}You can now run the shell simply typing {RED}`basilisk`{RESET}")

def main():
    print(f"{RED + BOLD} Starting setup for AI-Powered Basilisk Shell...{RESET}")
    install_system_packages()
    setup_virtualenv()
    install_python_packages()
    create_run_script()
    make_scripts_executable()
    create_symlink()
    print_final_message()

if __name__ == "__main__":
    main()
