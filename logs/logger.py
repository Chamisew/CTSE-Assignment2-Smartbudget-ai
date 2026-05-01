"""
Shared logging module for SmartBudget AI.
Every agent calls this to record its actions.
"""

import json
import os
from datetime import datetime


LOG_FILE = "logs/agent_logs.json"


def log_agent_action(
    agent_name: str,
    input_data: str,
    tool_called: str,
    output: str,
    status: str = "success"
) -> None:
    """
    Log an agent's action to the JSON log file.

    Args:
        agent_name: Name of the agent performing the action
        input_data: What the agent received as input
        tool_called: Name of the tool the agent used
        output: What the agent produced as output
        status: 'success' or 'error'
    """
    os.makedirs("logs", exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "status": status,
        "input": input_data,
        "tool_called": tool_called,
        "output": output
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"[LOG] {agent_name} → {tool_called} → {status}")