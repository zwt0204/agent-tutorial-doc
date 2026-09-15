"""Shared infrastructure for all chapters."""
import os
import subprocess
from pathlib import Path

WORKDIR = Path.cwd()
MAX_TURNS = 20


def get_client():
    from openai import OpenAI
    return OpenAI()


def get_model():
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def run_bash(command: str) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr


def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def estimate_tokens(messages: list) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += len(content) // 4
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    total += len(str(part.get("content", ""))) // 4
    return total
