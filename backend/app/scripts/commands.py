import click
from backend.app.scripts.init_tags import init_tags

@click.group()
def cli():
    pass

@cli.command()
def init_tags_command():
    """初始化标签系统"""
    init_tags()

if __name__ == "__main__":
    cli() 