import argparse
import sys

from protocol import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="txp-client",
        description="TXP/1.0 text client — browse Markdown pages over TCP.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "url", nargs="?", default="txp://localhost:9000/",
        help="server URL (default: txp://localhost:9000/)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="enable detailed logging"
    )
    return parser


def main_client(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"txp-client {__version__}")
    print(f"  url: {args.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main_client())
