import argparse
import sys

from protocol import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="txp-server",
        description="TXP/1.0 text server — serves Markdown pages over TCP.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="address to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=9000, help="port to listen on (default: 9000)"
    )
    parser.add_argument(
        "--docroot", "-d", default="./content", help="document root directory (default: ./content)"
    )
    parser.add_argument(
        "--config", "-c", default=None, help="path to configuration file"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="enable detailed logging"
    )
    return parser


def main_server(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"txp-server {__version__}")
    print(f"  host:    {args.host}")
    print(f"  port:    {args.port}")
    print(f"  docroot: {args.docroot}")
    return 0


if __name__ == "__main__":
    sys.exit(main_server())
