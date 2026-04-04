"""
BrowserPilot conversation memory for multi-turn AI queries.

Stores conversation history so ai_query can reference previous answers.
"""
import json
from pathlib import Path

CONVERSATION_FILE = Path.home() / ".browserpilot_profile" / ".conversation.json"
MAX_TURNS = 20  # Keep last N turns to avoid infinite growth


def load_conversation():
    """Load the conversation history."""
    if CONVERSATION_FILE.exists():
        try:
            data = json.loads(CONVERSATION_FILE.read_text())
            return data.get("messages", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_conversation(messages):
    """Save the conversation history, keeping only the last MAX_TURNS."""
    CONVERSATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    trimmed = messages[-MAX_TURNS * 2:]  # 2 messages per turn (user + assistant)
    CONVERSATION_FILE.write_text(json.dumps({"messages": trimmed}, indent=2))


def add_turn(user_message, assistant_message):
    """Add a user/assistant turn to the conversation."""
    messages = load_conversation()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": assistant_message})
    save_conversation(messages)


def clear_conversation():
    """Clear all conversation history."""
    if CONVERSATION_FILE.exists():
        CONVERSATION_FILE.unlink()
    return "Conversation history cleared."


def get_context_messages():
    """Get conversation history formatted for ollama chat."""
    return load_conversation()
