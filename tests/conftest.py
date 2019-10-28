import pytest
import inspect
import socket
from collections import namedtuple

from cqc.pythonLib import CQCConnection

Call = namedtuple("Call", ["name", "args", "kwargs"])


def _spy_wrapper(method):
    """Wraps a method to be able to spy on it"""
    def new_method(self, *args, **kwargs):
        if method.__name__ == '__init__':
            self.calls = []
        call = Call(method.__name__, args, kwargs)
        self.calls.append(call)
        return method(self, *args, **kwargs)

    return new_method


def spy_on_class(cls):
    """Spies on all calls to the methods of a class"""
    for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        setattr(cls, method_name, _spy_wrapper(method))
    return cls


@spy_on_class
class MockSocket:
    def __init__(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def send(self, *args, **kwargs):
        pass

    def recv(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass


@pytest.fixture
def mock_socket(monkeypatch):
    def get_mocked_socket(*args, **kwargs):
        mock_socket = MockSocket(*args, **kwargs)
        return mock_socket

    monkeypatch.setattr(socket, "socket", get_mocked_socket)


class MockedFirstMessage:
    """Mocks the second header returned by CQCConnection.readMessage"""
    class MockedTypeEntry:
        def __eq__(self, other):
            """This type will be equal to any integer."""
            return isinstance(other, int)

    @property
    def tp(self):
        return self.MockedTypeEntry()


class MockedOtherMessage:
    """Mocks the second header returned by CQCConnection.readMessage"""
    next_qubit_id = 0

    @property
    def qubit_id(self):
        qid = self.next_qubit_id
        self.next_qubit_id += 1
        return qid

    @property
    def outcome(self):
        return 0

    @property
    def datetime(self):
        return 0


@pytest.fixture
def mock_read_message(monkeypatch):
    """Mock the readMessage, check_error and print_CQC_msg from CQCConnection when testing."""
    def mocked_readMessage(self):
        return [MockedFirstMessage(), MockedOtherMessage()]

    def mocked_print_CQC_msg(self, message):
        pass

    def mocked_check_error(self, hdr):
        pass

    monkeypatch.setattr(CQCConnection, "readMessage", mocked_readMessage)
    monkeypatch.setattr(CQCConnection, "print_CQC_msg", mocked_print_CQC_msg)
    monkeypatch.setattr(CQCConnection, "check_error", mocked_check_error)
