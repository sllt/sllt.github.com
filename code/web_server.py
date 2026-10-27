#!/usr/bin/env python3
"""A simple extensible HTTP web server in Python 3 (with Case Handlers and CGI)."""

import mimetypes
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlsplit


class ServerException(Exception):
    """For internal error reporting."""


# ----------------------------------------------------------------------
# Case Handlers
# ----------------------------------------------------------------------


class base_case:
    """Parent for case handlers."""

    def handle_file(self, handler: "RequestHandler", full_path: str) -> None:
        try:
            with open(full_path, "rb") as reader:
                content = reader.read()
            content_type, _ = mimetypes.guess_type(full_path)
            handler.send_content(content, status=200, content_type=content_type or "text/html; charset=utf-8")
        except OSError as msg:
            msg_str = f"'{handler.path}' cannot be read: {msg}"
            handler.handle_error(msg_str)

    def index_path(self, handler: "RequestHandler") -> str:
        return os.path.join(handler.full_path, "index.html")

    def test(self, handler: "RequestHandler") -> bool:
        raise NotImplementedError

    def act(self, handler: "RequestHandler") -> None:
        raise NotImplementedError


class case_no_file(base_case):
    """File or directory does not exist."""

    def test(self, handler: "RequestHandler") -> bool:
        return not os.path.exists(handler.full_path)

    def act(self, handler: "RequestHandler") -> None:
        raise ServerException(f"'{handler.path}' not found")


class case_cgi_file(base_case):
    """Something runnable (.py script)."""

    def test(self, handler: "RequestHandler") -> bool:
        return os.path.isfile(handler.full_path) and handler.full_path.endswith(".py")

    def act(self, handler: "RequestHandler") -> None:
        handler.run_cgi(handler.full_path)


class case_existing_file(base_case):
    """File exists."""

    def test(self, handler: "RequestHandler") -> bool:
        return os.path.isfile(handler.full_path)

    def act(self, handler: "RequestHandler") -> None:
        self.handle_file(handler, handler.full_path)


class case_directory_index_file(base_case):
    """Serve index.html page for a directory."""

    def test(self, handler: "RequestHandler") -> bool:
        return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))

    def act(self, handler: "RequestHandler") -> None:
        self.handle_file(handler, self.index_path(handler))


class case_directory_no_index_file(base_case):
    """Serve listing for a directory without an index.html page."""

    def test(self, handler: "RequestHandler") -> bool:
        return os.path.isdir(handler.full_path) and not os.path.isfile(self.index_path(handler))

    def act(self, handler: "RequestHandler") -> None:
        handler.list_dir(handler.full_path)


class case_always_fail(base_case):
    """Base case if nothing else worked."""

    def test(self, handler: "RequestHandler") -> bool:
        return True

    def act(self, handler: "RequestHandler") -> None:
        raise ServerException(f"Unknown object '{handler.path}'")


# ----------------------------------------------------------------------
# Request Handler
# ----------------------------------------------------------------------


class RequestHandler(BaseHTTPRequestHandler):
    """
    If the requested path maps to a file, that file is served.
    If anything goes wrong, an error page is constructed.
    """

    Cases = [
        case_no_file(),
        case_cgi_file(),
        case_existing_file(),
        case_directory_index_file(),
        case_directory_no_index_file(),
        case_always_fail(),
    ]

    # How to display an error.
    Error_Page = """\
<html>
<body>
<h1>Error accessing {path}</h1>
<p>{msg}</p>
</body>
</html>
"""

    # How to display a directory listing.
    Listing_Page = """\
<html>
<body>
<ul>
{0}
</ul>
</body>
</html>
"""

    # Classify and handle request.
    def do_GET(self) -> None:
        try:
            # Parse URL path and resolve against current working directory.
            clean_path = unquote(urlsplit(self.path).path)
            root_dir = os.path.realpath(os.getcwd())
            self.full_path = os.path.realpath(os.path.join(root_dir, clean_path.lstrip("/")))

            # Prevent directory traversal outside root_dir.
            if os.path.commonpath([root_dir, self.full_path]) != root_dir:
                raise ServerException(f"Access denied: '{self.path}'")

            # Figure out how to handle it.
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break

        # Handle errors.
        except Exception as msg:
            self.handle_error(msg)

    def list_dir(self, full_path: str) -> None:
        try:
            entries = sorted(os.listdir(full_path))
            bullets = [f"<li>{e}</li>" for e in entries if not e.startswith(".")]
            page = self.Listing_Page.format("\n".join(bullets))
            self.send_content(page)
        except OSError as msg:
            msg_str = f"'{self.path}' cannot be listed: {msg}"
            self.handle_error(msg_str)

    def run_cgi(self, full_path: str) -> None:
        result = subprocess.run(
            [sys.executable, full_path],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            err_msg = result.stderr.decode("utf-8", errors="replace").strip()
            self.handle_error(f"CGI script failed: {err_msg or result.returncode}")
            return
        self.send_content(result.stdout)

    # Handle unknown objects.
    def handle_error(self, msg: object) -> None:
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content, 404)

    # Send actual content.
    def send_content(
        self,
        content: str | bytes,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
    ) -> None:
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


# ----------------------------------------------------------------------

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server_address = ("", port)
    server = HTTPServer(server_address, RequestHandler)
    print(f"Serving HTTP on http://localhost:{port} ...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
