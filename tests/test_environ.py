import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from io import TextIOBase
from tests.base import AsyncTestCase, noop_application


def environ_application(func):
    @wraps(func)
    def do_environ_application(environ, start_response):
        func(environ)
        return noop_application(environ, start_response)
    return do_environ_application


@environ_application
def assert_environ(environ):
    assert environ["REQUEST_METHOD"] == "GET"
    assert environ["SCRIPT_NAME"] == ""
    assert environ["PATH_INFO"] == "/"
    assert environ["CONTENT_TYPE"] == ""
    assert environ["CONTENT_LENGTH"] == "0"
    assert environ["SERVER_NAME"] == "127.0.0.1"
    assert int(environ["SERVER_PORT"]) > 0
    assert environ["REMOTE_ADDR"] == "127.0.0.1"
    assert environ["REMOTE_HOST"] == "127.0.0.1"
    assert int(environ["REMOTE_PORT"]) > 0
    assert environ["SERVER_PROTOCOL"] == "HTTP/1.1"
    assert environ["HTTP_FOO"] == "bar"
    assert environ["wsgi.version"] == (1, 0)
    assert environ["wsgi.url_scheme"] == "http"
    assert isinstance(environ["wsgi.errors"], TextIOBase)
    assert environ["wsgi.multithread"]
    assert not environ["wsgi.multiprocess"]
    assert not environ["wsgi.run_once"]
    assert isinstance(environ["asyncio.loop"], asyncio.BaseEventLoop)
    assert isinstance(environ["asyncio.executor"], ThreadPoolExecutor)
    assert "aiohttp.request" in environ


@environ_application
def assert_environ_post(environ):
    assert environ["REQUEST_METHOD"] == "POST"
    assert environ["CONTENT_TYPE"] == "text/plain"
    assert environ["CONTENT_LENGTH"] == "6"
    assert environ["wsgi.input"].read() == b"foobar"


@environ_application
def assert_environ_url_scheme(environ):
    assert environ["wsgi.url_scheme"] == "https"


@environ_application
def assert_environ_unix_socket(environ):
    assert environ["SERVER_NAME"] == "unix"
    assert environ["SERVER_PORT"].startswith("/")
    assert environ["REMOTE_HOST"] == "unix"
    assert environ["REMOTE_PORT"] == ""


@environ_application
def assert_environ_subdir(environ):
    assert environ["SCRIPT_NAME"] == ""
    assert environ["PATH_INFO"] == "/foo"


@environ_application
def assert_environ_root_subdir(environ):
    assert environ["SCRIPT_NAME"] == "/foo"
    assert environ["PATH_INFO"] == ""


@environ_application
def assert_environ_root_subdir_slash(environ):
    assert environ["SCRIPT_NAME"] == "/foo"
    assert environ["PATH_INFO"] == "/"


@environ_application
def assert_environ_root_subdir_trailing(environ):
    assert environ["SCRIPT_NAME"] == "/foo"
    assert environ["PATH_INFO"] == "/bar"


@environ_application
def assert_environ_quoted_path_info(environ):
    assert environ['PATH_INFO'] == "/테/스/트"
    assert environ['RAW_URI'] == "/%ED%85%8C%2F%EC%8A%A4%2F%ED%8A%B8"
    assert environ['REQUEST_URI'] == "/%ED%85%8C%2F%EC%8A%A4%2F%ED%8A%B8"


class EnvironTest(AsyncTestCase):

    def testEnviron(self):
        with self.run_server(assert_environ) as client:
            client.assert_response(headers={
                "Foo": "bar",
            })

    def testEnvironPost(self):
        with self.run_server(assert_environ_post) as client:
            client.assert_response(
                method="POST",
                headers={"Content-Type": "text/plain"},
                data=b"foobar",
            )

    def testEnvironUrlScheme(self):
        with self.run_server(assert_environ_url_scheme, url_scheme="https") as client:
            client.assert_response()

    def testEnvironUnixSocket(self):
        with self.run_server_unix(assert_environ_unix_socket) as client:
            client.assert_response()

    def testEnvironSubdir(self):
        with self.run_server(assert_environ_subdir) as client:
            client.assert_response(path="/foo")

    def testEnvironRootSubdir(self):
        with self.run_server(assert_environ_root_subdir, script_name="/foo") as client:
            client.assert_response(path="/foo")

    def testEnvironRootSubdirSlash(self):
        with self.run_server(assert_environ_root_subdir_slash, script_name="/foo") as client:
            client.assert_response(path="/foo/")

    def testEnvironRootSubdirTrailing(self):
        with self.run_server(assert_environ_root_subdir_trailing, script_name="/foo") as client:
            client.assert_response(path="/foo/bar")

    def testQuotedPathInfo(self):
        with self.run_server(assert_environ_quoted_path_info) as client:
            client.assert_response(path="/%ED%85%8C%2F%EC%8A%A4%2F%ED%8A%B8")
