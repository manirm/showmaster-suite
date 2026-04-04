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


if __name__ == "__main__":
    main_cli()
