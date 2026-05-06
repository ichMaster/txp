import pytest

from server.cli import build_parser as build_server_parser
from client.cli import build_parser as build_client_parser


class TestServerCLI:
    def test_defaults(self):
        parser = build_server_parser()
        args = parser.parse_args([])
        assert args.host == "0.0.0.0"
        assert args.port == 9000
        assert args.docroot == "./content"

    def test_port_override(self):
        parser = build_server_parser()
        args = parser.parse_args(["--port", "8080"])
        assert args.port == 8080

    def test_host_override(self):
        parser = build_server_parser()
        args = parser.parse_args(["--host", "127.0.0.1"])
        assert args.host == "127.0.0.1"

    def test_docroot_override(self):
        parser = build_server_parser()
        args = parser.parse_args(["--docroot", "/tmp/pages"])
        assert args.docroot == "/tmp/pages"

    def test_version(self, capsys):
        parser = build_server_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "0.1.0" in captured.out

    def test_help(self, capsys):
        parser = build_server_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0


class TestClientCLI:
    def test_defaults(self):
        parser = build_client_parser()
        args = parser.parse_args([])
        assert args.url == "txp://localhost:9000/"

    def test_custom_url(self):
        parser = build_client_parser()
        args = parser.parse_args(["txp://example.com:8080/page.md"])
        assert args.url == "txp://example.com:8080/page.md"

    def test_version(self, capsys):
        parser = build_client_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "0.1.0" in captured.out

    def test_help(self, capsys):
        parser = build_client_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0
