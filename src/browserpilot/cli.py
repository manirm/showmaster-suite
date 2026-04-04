"""
BrowserPilot CLI — persistent browser automation from the command line.

Uses Playwright's persistent context so browser state (cookies, history)
is maintained between commands via a user data directory.
No background server or CDP port is required.
"""
import click
from browserpilot.core import BrowserPilot


@click.group(name="browserpilot")
@click.option(
    "--headful", is_flag=True, default=False,
    help="Run browser in headful (visible) mode.",
)
@click.pass_context
def main_cli(ctx, headful):
    ctx.ensure_object(dict)
    ctx.obj["bp"] = BrowserPilot(headless=not headful)


@main_cli.command()
@click.argument("url")
@click.pass_context
def navigate(ctx, url):
    """Open a URL in the browser."""
    ctx.obj["bp"].open(url)


@main_cli.command()
@click.argument("selector")
@click.pass_context
def click_el(ctx, selector):
    """Click an element by CSS selector."""
    ctx.obj["bp"].click(selector)


@main_cli.command()
@click.argument("script")
@click.pass_context
def execute_js(ctx, script):
    """Execute JavaScript on the current page."""
    ctx.obj["bp"].js(script)


@main_cli.command()
@click.argument("path")
@click.pass_context
def snap(ctx, path):
    """Take a screenshot and save to PATH."""
    ctx.obj["bp"].screenshot(path)


@main_cli.command()
@click.argument("description")
@click.pass_context
def ai_click(ctx, description):
    """AI-powered click — describe what to click in plain English."""
    ctx.obj["bp"].ai_click(description)


@main_cli.command()
@click.argument("question")
@click.pass_context
def ai_query(ctx, question):
    """Ask AI a question about the current page content."""
    answer = ctx.obj["bp"].ai_query(question)
    click.echo(f"\nAI Answer:\n{answer}")


@main_cli.command()
@click.pass_context
def ai_clear(ctx):
    """Clear AI conversation history."""
    ctx.obj["bp"].ai_clear()


@main_cli.command()
@click.pass_context
def reset(ctx):
    """Clear the persistent browser profile (cookies, history, etc.)."""
    ctx.obj["bp"].reset()


@main_cli.command()
@click.argument("script_file")
@click.option("--speed", default=1.0, help="Playback speed multiplier (2.0 = 2x fast).")
@click.pass_context
def replay(ctx, script_file, speed):
    """Replay a recorded action script.

    SCRIPT_FILE is a .json file created by create-script or record-actions.
    """
    from browserpilot.recorder import replay_actions
    result = replay_actions(ctx.obj["bp"], script_file, speed=speed)
    click.echo(result)


@main_cli.command(name="create-script")
@click.argument("output_file")
def create_script_cmd(output_file):
    """Create an action script interactively.

    Enter actions one per line. Format: TYPE ARG
    Types: navigate URL, click SELECTOR, type SELECTOR TEXT, wait SECONDS,
           screenshot PATH, js SCRIPT, ai_click DESC, ai_query Q

    Press Ctrl+D (or Ctrl+Z on Windows) when done.
    """
    from browserpilot.recorder import ActionRecorder
    import sys

    recorder = ActionRecorder()
    recorder.start()
    click.echo("Enter actions (one per line). Ctrl+D to finish.\n")
    click.echo("  navigate https://example.com")
    click.echo("  wait 2")
    click.echo("  screenshot output.png")
    click.echo("  click #my-button")
    click.echo("  type #search hello world")
    click.echo("  ai_click Sign in button")
    click.echo("")

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            action_type = parts[0]
            arg = parts[1] if len(parts) > 1 else ""

            if action_type == "navigate":
                recorder.add_action("navigate", url=arg)
            elif action_type == "click":
                recorder.add_action("click", selector=arg)
            elif action_type == "type":
                sub = arg.split(maxsplit=1)
                recorder.add_action("type", selector=sub[0], text=sub[1] if len(sub) > 1 else "")
            elif action_type == "wait":
                recorder.add_action("wait", seconds=float(arg) if arg else 1)
            elif action_type == "screenshot":
                recorder.add_action("screenshot", path=arg or "screenshot.png")
            elif action_type == "js":
                recorder.add_action("js", script=arg)
            elif action_type == "ai_click":
                recorder.add_action("ai_click", description=arg)
            elif action_type == "ai_query":
                recorder.add_action("ai_query", question=arg)
            else:
                click.echo(f"  ⚠ Unknown action: {action_type}")
                continue

            click.echo(f"  ✓ {action_type}: {arg}")

    except (EOFError, KeyboardInterrupt):
        pass

    recorder.stop()
    result = recorder.save(output_file)
    click.echo(f"\n{result}")


if __name__ == "__main__":
    main_cli()

