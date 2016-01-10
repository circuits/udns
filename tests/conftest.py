"""Test Configuration and Fixtures"""


import threading
from time import sleep
from collections import deque


from pytest import fixture

from circuits.core.manager import TIMEOUT
from circuits import handler, BaseComponent, Debugger, Manager


from udns.server import (
    parse_args, parse_hosts, setup_database, setup_logging, Server
)

from .client import Client


class Watcher(BaseComponent):

    def init(self):
        self._lock = threading.Lock()
        self.events = deque()

    @handler(channel="*", priority=999.9)
    def _on_event(self, event, *args, **kwargs):
        with self._lock:
            self.events.append(event)

    def clear(self):
        self.events.clear()

    def wait(self, name, channel=None, timeout=6.0):
        try:
            for i in range(int(timeout / TIMEOUT)):
                if channel is None:
                    with self._lock:
                        for event in self.events:
                            if event.name == name:
                                return True
                else:
                    with self._lock:
                        for event in self.events:
                            if event.name == name and \
                                    channel in event.channels:
                                return True

                sleep(TIMEOUT)
        finally:
            self.events.clear()


class Flag(object):
    status = False


class WaitEvent(object):

    def __init__(self, manager, name, channel=None, timeout=6.0):
        if channel is None:
            channel = getattr(manager, "channel", None)

        self.timeout = timeout
        self.manager = manager

        flag = Flag()

        @handler(name, channel=channel)
        def on_event(self, *args, **kwargs):
            flag.status = True

        self.handler = self.manager.addHandler(on_event)
        self.flag = flag

    def wait(self):
        try:
            for i in range(int(self.timeout / TIMEOUT)):
                if self.flag.status:
                    return True
                sleep(TIMEOUT)
        finally:
            self.manager.removeHandler(self.handler)


def pytest_addoption(parser):
    parser.addoption(
        "--dbhost", action="store", default="localhost",
        help="Redis host to use for testing"
    )


@fixture(scope="session")
def dbhost(request):
    return request.config.getoption("--dbhost")


@fixture(scope="session")
def manager(request):
    manager = Manager()

    def finalizer():
        manager.stop()

    request.addfinalizer(finalizer)

    waiter = WaitEvent(manager, "started")
    manager.start()
    assert waiter.wait()

    if request.config.option.verbose:
        verbose = True
    else:
        verbose = False

    Debugger(events=verbose).register(manager)

    return manager


@fixture(scope="session")
def watcher(request, manager):
    watcher = Watcher().register(manager)

    def finalizer():
        waiter = WaitEvent(manager, "unregistered")
        watcher.unregister()
        waiter.wait()

    request.addfinalizer(finalizer)

    return watcher


@fixture(scope="session")
def server(request, manager, watcher, dbhost):
    argv = ["-b", "0.0.0.0:5300", "--debug", "--dbhost", dbhost]

    args = parse_args(argv)

    logger = setup_logging(args)

    db = setup_database(args, logger)

    hosts = parse_hosts("/etc/hosts")

    server = Server(args, db, hosts, logger)

    server.register(manager)
    watcher.wait("ready")

    def finalizer():
        server.unregister()

    request.addfinalizer(finalizer)

    return server


@fixture(scope="session")
def client(request, manager, watcher, server):
    client = Client("127.0.0.1", 5300)

    client.register(manager)
    watcher.wait("ready")

    def finalizer():
        client.unregister()

    request.addfinalizer(finalizer)

    return client
