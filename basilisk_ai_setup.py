#!/usr/bin/env python3
from groq import Groq
import os
from dotenv import load_dotenv
import subprocess
import shlex
import json
import datetime
import sys
import time

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

# Cursor shapes 
CURSOR_BLOCK = "\033[2 q"   
CURSOR_BAR   = "\033[6 q"   

def colour(text: str, col: str) -> str:
    return f"{col}{text}{RESET}"

# function to Load API Key
def load_api_key():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, ".env")

    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            print(f"{MINT}API Key loaded successfully.{RESET}")
            return api_key
        else:
            print(f"{RED + BOLD}Key 'GROQ_API_KEY' missing in '{dotenv_path}'.{RESET}")
    else:
        print(f"{RED + BOLD}No '{".env"}' file found at '{dotenv_path}'.{RESET}")

    # if we got here, we need to ask the user for the key.
    print(f"{YELLOW}Please enter your Groq API Key (will be saved to '{dotenv_path}'):{RESET}")
    api_key = input(f"{GREEN}Paste key here: {RESET}").strip()
    if not api_key:
        print(f"{RED}No API key entered. Exiting.{RESET}")
        sys.exit(1)
    try:
        with open(dotenv_path, "w") as f:
            f.write(f"GROQ_API_KEY={api_key}\n")
        print(f"{MINT + BOLD}API key saved to '{dotenv_path}'.{RESET}")
        # also set it as an environment variable for this current script run.
        os.environ["GROQ_API_KEY"] = api_key
    except Exception as e:
        print(f"{RED}Error saving API key to '{dotenv_path}': {e}.{RESET}")
        api_key = os.getenv("GROQ_API_KEY", api_key) 

    if not api_key: 
         print(f"{RED}Could not obtain API key. Exiting.{RESET}")
         sys.exit(1)
    return api_key

# function to setup Groq AI
def configure_ai(api_key):
    try:
        client = Groq(api_key=api_key)
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print(f"{MINT}Groq AI configured successfully (using Llama 3.3 70B)!{RESET}")
        return client
    except Exception as e:
        print(f"{RED}\n--- FATAL AI CONFIGURATION ERROR ---{RESET}")
        print(f"{RED}Error details: {e}{RESET}")
        
        if "invalid" in str(e).lower() or "authentication" in str(e).lower() or "api key" in str(e).lower():
             print(f"{RED}Your Groq API Key appears INVALID. Please check or replace '{".env"}'.{RESET}")
             # if the key is bad, maybe try deleting the .env file so the user is prompted again next time.
             script_dir = os.path.dirname(os.path.abspath(__file__))
             dotenv_path = os.path.join(script_dir, ".env")
             if os.path.exists(dotenv_path):
                 try:
                     os.remove(dotenv_path)
                     print(f"{YELLOW}Removed the potentially invalid '{".env"}'. Please restart the script to enter a new key.{RESET}")
                 except Exception as rm_err:
                     print(f"{YELLOW}Could not remove '{".env"}': {rm_err}{RESET}")
        elif "rate" in str(e).lower() or "quota" in str(e).lower():
            print(f"{YELLOW}You might have exceeded your API usage quota. Check your Groq Cloud console.{RESET}")
        elif "permission" in str(e).lower():
            print(f"{YELLOW}Permission denied. Ensure the API key is valid and active on Groq Cloud.{RESET}")
        else:
            print(f"{YELLOW}This could be a network issue, an API outage, or another configuration problem.{RESET}")

        # can't proceed without a working ai connection.
        print(f"{RED}Cannot continue without a valid AI configuration. Exiting.{RESET}")
        sys.exit(1)

# define AI prompts and security blocklists
base_prompt = """
You are an AI assistant that generates accurate Linux Bash commands based on user requests.
The input request may be written in any language (such as English, Bangla, Urdu, Hindi, Arabic, Spanish, etc.),
and you must intelligently understand and interpret the task regardless of the language used.

You must respond ONLY with a single valid JSON object — no markdown, no explanation outside JSON, no greetings, no extra text.

The JSON schema is:
{
  "command": "<the exact bash command to run>",
  "explanation": "<1-2 sentence plain English description of what the command does and any key options used>",
  "risk_level": "low | medium | high"
}

Risk level guidance:
- low    : read-only, no system changes, no elevated privileges
- medium : writes files, restarts services, modifies configs
- high   : deletes data, modifies system files, system config change, require sudo/root privileges to run, irreversible

Keep the command simple and correct by default, unless the user specifically requests a complex operation. If complexity is required, ensure that the use of pipes or logical operators still fits neatly on a single command line. Regardless of the input language, always detect the intent properly and respond as if the request were made in English. The explanation must always remain in English only for consistency, even if the request is in another language.

Example Request in English:
Request: list files with details
Response:
{"command": "ls -lah", "explanation": "Lists all files (including hidden) in long format with human-readable sizes.", "risk_level": "low"}

Example Request in Bangla:
Request: বিস্তারিত সহ সমস্ত ফাইল দেখান
Response:
{"command": "ls -lah", "explanation": "Lists all files (including hidden) in long format with human-readable sizes.", "risk_level": "low"}

Never include code fences, comments, or any text outside the JSON object.

The task is : {INPUT}

"""
BLOCKLIST = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",
    ">(){ ",
    "chmod -R 777 /",
    "chmod 777 /",
    "> /dev/sda",
    "curl | bash",
    "wget | bash",
    "curl | sh",
    "wget | sh",
]
WARN_PATTERNS = {
    "sudo":       "elevated privilege",
    "wildcard":   "filesystem wildcard",
    "chaining":   "command chaining",
}

# asks the ai if a given command might be risky to run
def security_audit(command):
    """Returns (blocked: bool, warnings: list[str], effective_risk: str)"""
    cmd_lower = command.lower().strip()
    warnings  = []

    # hard block
    for pattern in BLOCKLIST:
        if pattern.lower() in cmd_lower:
            return True, [f"Blocked pattern detected: `{pattern}`"], "high"
    # warn patterns
    if "sudo" in cmd_lower:
        warnings.append("Uses `sudo` (elevated privileges)")
    # wildcards
    if "*" in command or "?" in command:
        warnings.append("Contains wildcard characters (* ?)")
    # chaining operators
    for op in [";", "&&", "||"]:
        if op in command:
            warnings.append(f"Contains command chaining operator `{op}`")
            break
    # pipe
    if "|" in command:
        warnings.append("Contains pipe `|`")
        
    effective_risk = "high" if warnings else None
    return False, warnings, effective_risk 

# this talks to the ai to get the actual command and its explanation based on what the user asked for.
def get_command_and_explanation(client, user_input):
    """Gets command/explanation from AI (Groq Llama 3.3 70B). Returns (command, explanation, risk_level, error_msg)."""
    if not user_input.strip(): 
        return None, None, None, f"{RED}Input request is empty.{RESET}"
    
    prompt = base_prompt.replace("{INPUT}", user_input)
    print(colour("\n  ◌  Thinking…", GREY), end="\r")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2
        )

        response_text = response.choices[0].message.content if response.choices else None
        if not response_text or not response_text.strip():
            return None, None, None, f"{RED}AI response was empty.{RESET}"
        
        raw = response_text.strip()

        # parse JSON response
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None, None, None, f"{RED}AI returned non-JSON output:\n{raw}{RESET}"

        # validate required fields
        required = {"command", "explanation", "risk_level"}
        missing = required - data.keys()
        if missing:
            return None, None, None, f"{RED}AI response missing required fields: {missing}{RESET}"

        command = data["command"].strip()
        explanation = data["explanation"].strip()
        risk_level = data["risk_level"].strip().lower()

        if risk_level not in ("low", "medium", "high"):
            print(f"{YELLOW + BOLD}Warning: Invalid risk_level '{risk_level}' from AI. Defaulting to 'high'.{RESET}")
            risk_level = "high"

        if not command:
            return None, None, None, f"{RED}AI response contained an empty command.{RESET}"

        return command, explanation, risk_level, None
    except json.JSONDecodeError:
        return None, None, None, f"{RED}AI returned non-JSON output.{RESET}"
    except Exception as e:
        print(f"{RED}Error communicating with AI: {e}{RESET}")
        return None, None, None, f"{RED}Failed to get command due to API communication error.{RESET}"

# asks the ai to explain a specific command or topic the user typed.
def explain_command(client, command_input):
    prompt = f"""
Imagine you're explaining the following Linux concept or command
to someone who's new to Linux. Make the explanation clear, concise,
and easy to understand. Focus on the main purpose, common usage,
and why someone would use this command in real-world scenarios.
If the command is part of the explanation, include it clearly with a brief example.
Format the output as follows:

Imagine this: (2-3 lines describing the context or scenario where the command would be used)
Explanation: (2-3 lines explaining the command's main purpose, how it works, and why it's useful)
Command: (The actual Linux command for clarity)
Example: (A practical example to show how the command is used with output or a scenario)

Here is the concept or command I want to explain:

{command_input}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
       
        response_text = response.choices[0].message.content if response.choices else None
        if response_text and response_text.strip():
            return response_text.strip()
        else:
             return f"{RED}Couldn't get explanation (AI gave empty response).{RESET}"
    except Exception as e:
        print(f"{RED}Explain command API error: {e}{RESET}")
        return f"{RED}Error occurred while trying to get explanation.{RESET}"

# function to execute command
def execute_command(command: str) -> int:
    """Safely execute a command using subprocess.run."""
    try:
        args = shlex.split(command)
    except ValueError as e:
        print(f"{RED}     Failed to parse command: {e}{RESET}")
        return 1

    print()
    print(colour("  Executing…", CYAN))

    try:
        result = subprocess.run(
            args,
            shell=False,        
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(colour("     Command timed out after 30 seconds.", RED))
        return 1
    except FileNotFoundError:
        print(colour(f"     Command not found: `{args[0]}`", RED))
        return 1
    except PermissionError:
        print(colour(f"     Permission denied.", RED))
        return 1

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(colour(result.stderr, YELLOW), end="")

    if result.returncode == 0:
        print(colour(f"\n  ✔  Done (exit 0)", GREEN))
    else:
        print(colour(f"\n  Exited with code {result.returncode}", RED))

    return result.returncode

# function to confirm execution
def confirm(risk: str) -> bool:
    if risk == "high":
        print()
        print(colour("  ⛔  HIGH RISK COMMAND", RED + BOLD))
        print(colour('  Type exactly YES to proceed:', RED))
        ans = input(colour("  > ", RED)).strip()
        return ans == "YES"
    else:
        ans = input(colour("  Execute? [y/N] ", CYAN)).strip().lower()
        return ans in ("y", "yes")

# function to log command history 
def logging_command_history(ai_generated_command, user_input_request, risk_level, status):
    """Logs commands to the basilisk_cmd_history.log."""
    try:
        # find the directory where this script is running.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # define the log file path in the same directory.
        log_path = os.path.join(script_dir, "basilisk_cmd_history.log")
        # open the log file in append mode ('a') with utf-8 encoding.
        with open(log_path, "a", encoding='utf-8') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_request = user_input_request.replace("'", "\\'")
            safe_command = ai_generated_command.replace("'", "\\'")
            
            f.write(f"[{timestamp}] Request: '{safe_request}', Running: '{safe_command}', Risk: {risk_level}, Status: {status}\n")
    except Exception as e: 
        print(f"{RED}Log write error to {log_path}: {e}{RESET}")


# display helpers
def print_status_bar():
    """Prints the bottom status bar — model and history path"""
    right = colour("Llama-3.3-70b-versatile", MINT + BOLD) + colour("  (type /history for log)", GREY)
    print(f"                                                  {right}")
    print()

def print_tips():
    print()
    print(f"  {BOLD}{WHITE}Tips for getting started:{RESET}")
    print(f"  1. Describe any task in plain English — BasiliskShell finds the command.")
    print(f"  2. Be specific for the best results.")
    print(f"  3. {colour('high', RED + BOLD)} risk commands require typing {colour('YES', RED)} to run.")
    print(f"  4. Type {colour('/history', MINT)} for past commands  •  {colour('exit', MINT)} to quit.")
    print()
    print_status_bar()

def display_result(data: dict, warnings: list[str]):
    risk = data["risk_level"].lower()
    if risk == "low": risk_col = GREEN
    elif risk == "medium": risk_col = YELLOW
    elif risk == "high": risk_col = RED
    badge = f" {risk.upper()} "

    print()
    print()
    print(colour("  Command     ", YELLOW + BOLD) + colour(data["command"], BOLD + WHITE))
    print(colour("  Explanation ", YELLOW + BOLD) + data["explanation"])
    print(colour("  Risk        ", YELLOW + BOLD) + colour(badge, BOLD + risk_col))
    print()

    if warnings:
        print(colour("", CYAN))
        print(colour("  Warnings", YELLOW))
        for w in warnings:
            print(colour("    ⚠  ", YELLOW) + colour(w, YELLOW))


# main program
def main():
    # Load API and configure AI
    api_key = load_api_key()
    client = configure_ai(api_key)
    print_tips()
    
    # switch to block cursor when the shell starts
    sys.stdout.write(CURSOR_BLOCK)
    sys.stdout.flush()
    while True:
        try:
            user_input = input(colour("  > ", CYAN + BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write(CURSOR_BAR)
            sys.stdout.flush()
            print(colour("\n  Goodbye.\n", GREY))
            sys.exit(0)

        if user_input.lower() in ("exit", "quit", "q"):
            sys.stdout.write(CURSOR_BAR)
            sys.stdout.flush()
            print(colour("\n  Goodbye.\n", GREY))
            sys.exit(0)

        if user_input.startswith("#") or not user_input:
            continue

        user_input_lower = user_input.strip().lower()
        if not user_input_lower:
            continue

        # /history slash command
        if user_input_lower == "/history":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(script_dir, "basilisk_cmd_history.log")
            if os.path.exists(log_path):
                print()
                with open(log_path, "r", encoding="utf-8") as f:
                    print(f.read())
            else:
                print(colour("  No history yet.", GREY))
            print()
            continue

        # explain command
        explain_triggered = False
        topic_to_explain = ""
        explain_prefixes = ("explain ", "what is ", "what's ", "tell me about ", "describe ")
        for prefix in explain_prefixes:
            if user_input.startswith(prefix):
                if len(user_input) > len(prefix):
                    topic_to_explain = user_input[len(prefix):].strip()
                    explain_triggered = True
                    break
                else:
                    print(f"{YELLOW}Please specify what you want explained after '{prefix.strip()}'.{RESET}")
                    explain_triggered = True
                    topic_to_explain = None

        if explain_triggered:
            if topic_to_explain:
                print(colour("\n  ◌  Thinking…", GREY), end="\r")
                explanation_text = explain_command(client, topic_to_explain)
                print(f"{YELLOW + BOLD}AI Explanation:\n{RESET}")
                print(colour(explanation_text, MINT))
            continue

        # AI command generation and explanation
        ai_generated_command, explanation_from_ai, command_risk_level, error_msg = get_command_and_explanation(client, user_input)
        if error_msg:
            print(error_msg)
        if not ai_generated_command:
            print(f"{RED}AI did not provide a valid command.{RESET}")
            continue

        data = {
            "command": ai_generated_command,
            "explanation": explanation_from_ai,
            "risk_level": command_risk_level
        }
 
        # security check 
        blocked, warnings, escalated_risk = security_audit(ai_generated_command)

        if blocked:
            print(colour(f"\n  🚫  BLOCKED: {warnings[0]}", RED + BOLD))
            logging_command_history(ai_generated_command, user_input, "high", "BLOCKED")
            continue

        if escalated_risk == "high" and command_risk_level != "high":
            data["risk_level"] = "high"
            risk = "high"

        # display result
        display_result(data, warnings)
        
        # confirm before execution
        if not confirm(command_risk_level):
            print(colour("  Cancelled.", GREY))
            logging_command_history(ai_generated_command, user_input, command_risk_level , "CANCELLED")
            continue

        # execution of command
        rc = execute_command(ai_generated_command)
        logging_command_history(ai_generated_command, user_input, command_risk_level , f"EXIT_{rc}")
        print()

if __name__ == "__main__":
    main()