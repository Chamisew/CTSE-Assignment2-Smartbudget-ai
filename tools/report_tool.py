"""
Tool for generating and saving the final financial report.
Member 4's custom tool.
"""

import os
from datetime import datetime
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from logs.logger import log_agent_action
