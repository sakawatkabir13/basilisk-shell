#!/bin/bash
# theme colors
GREEN="\e[32m"
CYAN="\e[36m"
YELLOW="\e[33m"
RED="\e[31m"
MAGENTA="\e[35m"
BLUE="\e[34m"
GOLD="\e[38;5;220m"
C1="\e[38;2;120;180;255m"
C2="\e[38;2;120;220;220m"
C3="\e[38;2;120;255;180m"
C4="\e[38;2;150;255;150m"
DIM="\e[2m"
BOLD="\e[1m"
RESET="\e[0m"

USER_FILE="$HOME/.basilisk_user"
PASS_FILE="$HOME/.basilisk_pass"
HISTORY_FILE="$HOME/.basilisk_history"

# loading
loading() {
    echo -ne "${GOLD}Initializing Basilisk"
    for i in {1..3}; do
        sleep 0.4
        echo -ne "."
    done
    echo -e "${RESET}"
}

# banner
show_banner() {
    clear

    echo
    echo -e "${DIM}${C1}      ██████╗  █████╗ ███████╗██╗██╗     ██╗███████╗██╗  ██╗${RESET}"
    echo -e "${C1}      ██╔══██╗██╔══██╗██╔════╝██║██║     ██║██╔════╝██║ ██╔╝${RESET}"
    echo -e "${C2}      ██████╔╝███████║███████╗██║██║     ██║███████╗█████╔╝ ${RESET}"
    echo -e "${C3}      ██╔══██╗██╔══██║╚════██║██║██║     ██║╚════██║██╔═██╗ ${RESET}"
    echo -e "${BOLD}${C4}      ██████╔╝██║  ██║███████║██║███████╗██║███████║██║  ██╗${RESET}"
    echo -e "${DIM}${C4}      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═╝${RESET}"

    echo
    echo -e "${C2}              🐍  B A S I L I S K   S H E L L  🐍${RESET}"
    echo -e "${C3}             AI-Powered Linux Terminal Assistant${RESET}"
    echo -e "${C4}                    The Revolution Begins${RESET}"
    echo -e "${GOLD}                 Developed by: Sakawat Kabir${RESET}"
    echo
}

# prompt 
prompt() {
    user=$(cat "$USER_FILE")
    echo -ne "\n${RED}⚔ [basilisk${YELLOW}@${C3}$user${RED}]─[${GREEN}$(pwd)${RED}]\n${RED}└──╼${YELLOW} #${RESET}"
}

# help Menu
show_help() {
    clear
    echo -e "${CYAN}══════════ BASILISK COMMAND CENTER ══════════${RESET}"
    echo -e "${GREEN}system${RESET}                → View system status"
    echo -e "${GREEN}system live${RESET}           → Live system monitor"
    echo -e "${GREEN}aibasilisk${RESET}            → Call Basilisk AI 🤖"
    echo -e "${GREEN}history${RESET}               → Show command history"
    echo -e "${GREEN}clear${RESET}                 → Clear screen"
    echo -e "${GREEN}exit${RESET}                  → Exit Basilisk"
    echo -e "${CYAN}════════════════════════════════════════════${RESET}"
}

# first time setup
first_time_setup() {
    clear
    echo -e "${CYAN}══════════ BASILISK INITIAL SETUP ══════════${RESET}"

    read -p "Create username: " username
    while true; do
        read -s -p "Create password: " pass1
        echo
        read -s -p "Confirm password: " pass2
        echo

        [[ "$pass1" == "$pass2" ]] && break
        echo -e "${RED}Passwords do not match. Please try again.${RESET}"
    done

    echo "$username" > "$USER_FILE"
    echo -n "$pass1" | sha256sum | awk '{print $1}' > "$PASS_FILE"
    echo -e "${GREEN}User created successfully!${RESET}"
    sleep 1
}

# login
login() {
    clear
    echo -e "${CYAN}══════════ BASILISK LOGIN ══════════${RESET}"

    username=$(cat "$USER_FILE")
    for attempt in {1..3}; do
        read -s -p "Password: " pass
        echo
        input_hash=$(echo -n "$pass" | sha256sum | awk '{print $1}')
        stored_hash=$(cat "$PASS_FILE")

        if [[ "$input_hash" == "$stored_hash" ]]; then
            echo -e "${GREEN}Access Granted. Welcome, $username.${RESET}"
            sleep 1
            return
        else
            echo -e "${RED}Incorrect password.${RESET}"
        fi
    done

    echo -e "${RED}Too many failed attempts. Exiting.${RESET}"
    exit 1
}

# system Monitor
system_monitor() {
    echo -e "${CYAN}──────── BASILISK SYSTEM STATUS ────────${RESET}"

    cpu_idle=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}')
    cpu_used=$(echo "100 - $cpu_idle" | bc)

    mem_used=$(free -h | awk '/Mem:/ {print $3}')
    mem_total=$(free -h | awk '/Mem:/ {print $2}')

    disk_usage=$(df -h / | awk 'NR==2 {print $5}')

    top_proc=$(ps -eo pid,comm,%mem --sort=-%mem | awk 'NR==2 {print $2 " (PID " $1 ")"}')

    echo -e "${GREEN}CPU Usage     ${RESET}: ${YELLOW}${cpu_used}%${RESET}"
    echo -e "${GREEN}Memory Usage  ${RESET}: ${YELLOW}$mem_used / $mem_total${RESET}"
    echo -e "${GREEN}Disk Usage    ${RESET}: ${YELLOW}$disk_usage${RESET}"
    echo -e "${GREEN}Top Process   ${RESET}: ${YELLOW}$top_proc${RESET}"
}

system_live() {
    while true; do
        clear
        system_monitor
        sleep 2
    done
}

# call AI 
basilisk_ai() {
    clear
    echo 
    echo -e "${CYAN}🤖 Basilisk AI${RESET}"
    echo -e "${CYAN}────────────────${RESET}"
    SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
    bash "$SCRIPT_DIR/run.sh"
}

# main startup
loading

if [[ ! -f "$USER_FILE" || ! -f "$PASS_FILE" ]]; then
    first_time_setup
else
    login
fi

show_banner

# main Loop
while true; do
    prompt
    read cmd

    # ignore empty input
    if [[ -z "$cmd" ]]; then
        continue
    fi

    # save command to history
    echo "$cmd" >> "$HISTORY_FILE"

    # exit
    [[ "$cmd" == "exit" ]] && break

    # built-ins
    [[ "$cmd" == "clear" ]] && clear && continue
    [[ "$cmd" == "help" ]] && show_help && continue
    [[ "$cmd" == "history" ]] && nl "$HISTORY_FILE" && continue

    # cd Handling
    if [[ "$cmd" == "cd" || "$cmd" == cd\ * ]]; then
        dir="${cmd#cd }"

        if [[ -z "$dir" || "$dir" == "cd" ]]; then
            cd ~ || echo "Failed to change directory"
        else
            eval cd "$dir" 2>/dev/null || echo -e "${RED}Directory not found${RESET}"
        fi
        continue
    fi

    # system monitor Handling
    [[ "$cmd" == "system" ]] && system_monitor && read -p "Press Enter..." && continue
    [[ "$cmd" == "system live" ]] && system_live && continue

    # pipe handling
    if [[ "$cmd" == *"|"* ]]; then
        bash -c "$cmd"
        continue
    fi

    # AI Handling
    [[ "$cmd" =~ ai|aibasilisk|aishell|basiliskai ]] && basilisk_ai && continue

    # background job detection
    if [[ "$cmd" == *"&" ]]; then
        bg_cmd="${cmd/&/}"
        eval "$bg_cmd" &
        echo "Started background job with PID: $!"
        continue
    fi

    # execute external commands
    eval "$cmd"
done

echo -e "${CYAN}Goodbye from Basilisk 🐍${RESET}"
