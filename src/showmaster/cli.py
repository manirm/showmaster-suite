import click
from showmaster.core import Showmaster

@click.group()
@click.option('--file', '-f', default='demo.md', help='Target markdown file.')
@click.pass_context
def cli(ctx, file):
    ctx.obj = Showmaster(file)

@cli.command()
@click.argument('title')
@click.pass_obj
def init(sm, title):
    """Initialize a new demo markdown file."""
    sm.init(title)
    click.echo(f"Initialized {sm.filepath} with title: {title}")

@cli.command()
@click.argument('text')
@click.pass_obj
def note(sm, text):
    """Add a note to the demo."""
    sm.note(text)
    click.echo(f"Added note to {sm.filepath}")

@cli.command()
@click.argument('command')
@click.option('--shell', default='bash', help='Shell to use.')
@click.pass_obj
def exec(sm, command, shell):
    """Execute a command and append output."""
    output = sm.exec(command, shell)
    click.echo(f"Executed: {command}")
    click.echo(output)

@cli.command()
@click.argument('command')
@click.option('--shell', default='bash', help='Shell to use.')
@click.pass_obj
def image(sm, command, shell):
    """Execute command and capture output image."""
    sm.image(command, shell)
    click.echo(f"Executed image command: {command}")

@cli.command()
@click.pass_obj
def pop(sm):
    """Remove the most recently added section."""
    sm.pop()
    click.echo(f"Popped last section from {sm.filepath}")

@cli.command()
@click.pass_obj
def extract(sm):
    """Extract all exec commands from the demo."""
    commands = sm.extract()
    for cmd in commands:
        click.echo(cmd)

@cli.command()
@click.argument('url')
@click.pass_obj
def browser_snap(sm, url):
    """Capture a screenshot of a web page using BrowserPilot."""
    msg = sm.browser_snap(url)
    click.echo(msg)

@cli.command()
@click.pass_obj
def finalize(sm):
    """Finalize the report by adding a TOC and license info."""
    msg = sm.finalize()
    click.echo(msg)

@cli.command()
@click.option('--duration', default=10, help='Recording duration in seconds.')
@click.pass_obj
def record(sm, duration):
    """Record a video (short demo)."""
    import time
    click.echo(f"Starting recording for {duration} seconds...")
    sm.start_record()
    time.sleep(duration)
    msg = sm.stop_record()
    click.echo(msg)

if __name__ == '__main__':
    cli()
