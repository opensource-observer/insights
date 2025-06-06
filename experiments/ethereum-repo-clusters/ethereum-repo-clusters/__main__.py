from .cli.main_cli import cli

def main():
    # The obj={} is a way to initialize Click's context object
    # if it's not being run directly by the `click` runner (e.g. `python -m devtooling_labels`)
    cli(obj={})

if __name__ == "__main__":
    main()
