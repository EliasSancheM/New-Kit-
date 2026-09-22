"""
Claude CLI Persistent Bridge Utility
------------------------------------
Maintains a dedicated, persistent session ID for Antigravity <-> Claude Code
communication, completely isolated from user interactive sessions.
"""

import sys
import os
import subprocess
import json

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_SESSION_ID = "51ac3ac2-3526-44d6-8edb-1972561a3454"

def get_session_id() -> str:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "claude_session_id" in data:
                    return data["claude_session_id"]
        except Exception:
            pass
    return DEFAULT_SESSION_ID

def send_to_claude(prompt: str) -> str:
    session_id = get_session_id()
    
    # 1. Try to resume existing session
    cmd_resume = f'claude --resume {session_id} -p'
    try:
        proc = subprocess.Popen(
            cmd_resume,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True
        )
        stdout, stderr = proc.communicate(input=prompt, timeout=120)
        if proc.returncode == 0:
            return stdout.strip()
    except Exception:
        pass

    # 2. If resume fails, initialize with session-id
    cmd_init = f'claude --session-id {session_id} -p'
    proc = subprocess.Popen(
        cmd_init,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True
    )
    stdout, stderr = proc.communicate(input=prompt, timeout=120)
    return stdout.strip()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = sys.stdin.read()

    if not msg.strip():
        print("Usage: python claude_bridge.py <prompt>")
        sys.exit(1)

    reply = send_to_claude(msg)
    print(reply)
