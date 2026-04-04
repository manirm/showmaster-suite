"""
BrowserPilot Action Recorder — Record and replay browser interactions.

Records user-defined actions as a JSON script, then replays them.
Useful for regression testing, demos, and automation workflows.
"""
import json
import time
from pathlib import Path


class ActionRecorder:
    """Records a sequence of browser actions for later playback."""

    def __init__(self):
        self.actions = []
        self.recording = False
        self.start_time = None

    def start(self):
        """Start recording actions."""
        self.actions = []
        self.recording = True
        self.start_time = time.time()
        return "Recording started."

    def stop(self):
        """Stop recording and return the action list."""
        self.recording = False
        self.start_time = None
        return f"Recording stopped. {len(self.actions)} actions captured."

    def add_action(self, action_type, **kwargs):
        """Add an action to the recording."""
        if not self.recording:
            return
        elapsed = time.time() - self.start_time if self.start_time else 0
        action = {
            "type": action_type,
            "timestamp": round(elapsed, 2),
            **kwargs,
        }
        self.actions.append(action)

    def save(self, filepath):
        """Save the recorded actions to a JSON file."""
        path = Path(filepath)
        data = {
            "version": "1.0",
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "action_count": len(self.actions),
            "actions": self.actions,
        }
        path.write_text(json.dumps(data, indent=2))
        return f"Saved {len(self.actions)} actions to {filepath}"

    def load(self, filepath):
        """Load actions from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Script not found: {filepath}")
        data = json.loads(path.read_text())
        self.actions = data.get("actions", [])
        return f"Loaded {len(self.actions)} actions from {filepath}"


def replay_actions(bp, filepath, speed=1.0, verbose=True):
    """
    Replay a recorded action script against a BrowserPilot instance.

    Args:
        bp: BrowserPilot instance
        filepath: Path to the JSON script file
        speed: Playback speed multiplier (1.0 = real-time, 2.0 = 2x fast)
        verbose: Print each action as it executes
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {filepath}")

    data = json.loads(path.read_text())
    actions = data.get("actions", [])

    if verbose:
        print(f"Replaying {len(actions)} actions (speed: {speed}x)...")

    last_timestamp = 0

    for i, action in enumerate(actions, 1):
        # Wait for the appropriate delay
        delay = (action["timestamp"] - last_timestamp) / speed
        if delay > 0:
            time.sleep(delay)
        last_timestamp = action["timestamp"]

        action_type = action["type"]

        if verbose:
            print(f"  [{i}/{len(actions)}] {action_type}: {_describe_action(action)}")

        if action_type == "navigate":
            bp.open(action["url"])

        elif action_type == "click":
            bp.click(action["selector"])

        elif action_type == "type":
            # Type text into an element
            from playwright.sync_api import sync_playwright
            from browserpilot.core import USER_DATA_DIR
            USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    user_data_dir=str(USER_DATA_DIR),
                    headless=bp.headless,
                )
                try:
                    page = ctx.pages[0] if ctx.pages else ctx.new_page()
                    state = bp._load_state()
                    last_url = state.get("last_url")
                    if last_url and page.url in ("about:blank", ""):
                        page.goto(last_url)
                    page.fill(action["selector"], action["text"])
                finally:
                    ctx.close()

        elif action_type == "screenshot":
            bp.screenshot(action.get("path", "replay_screenshot.png"))

        elif action_type == "js":
            bp.js(action["script"])

        elif action_type == "wait":
            time.sleep(action.get("seconds", 1))

        elif action_type == "ai_click":
            bp.ai_click(action["description"])

        elif action_type == "ai_query":
            bp.ai_query(action["question"])

        else:
            if verbose:
                print(f"  ⚠ Unknown action type: {action_type}")

    if verbose:
        print(f"Replay complete: {len(actions)} actions executed.")

    return f"Replayed {len(actions)} actions from {filepath}"


def _describe_action(action):
    """Human-readable description of an action."""
    t = action["type"]
    if t == "navigate":
        return action.get("url", "")
    elif t == "click":
        return action.get("selector", "")
    elif t == "type":
        return f"{action.get('selector', '')} ← '{action.get('text', '')}'"
    elif t == "screenshot":
        return action.get("path", "screenshot.png")
    elif t == "js":
        return action.get("script", "")[:60]
    elif t == "wait":
        return f"{action.get('seconds', 1)}s"
    elif t == "ai_click":
        return action.get("description", "")
    elif t == "ai_query":
        return action.get("question", "")
    return str(action)


def create_script(actions_list, filepath):
    """
    Programmatically create an action script.

    Example:
        create_script([
            {"type": "navigate", "url": "https://example.com"},
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "path": "result.png"},
        ], "my_test.json")
    """
    recorder = ActionRecorder()
    recorder.actions = [
        {"type": a["type"], "timestamp": i * 1.0, **{k: v for k, v in a.items() if k != "type"}}
        for i, a in enumerate(actions_list)
    ]
    return recorder.save(filepath)
