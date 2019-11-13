import pytest

from cqc.pythonLib import CQCConnection, qubit
from cqc.cqcHeader import CQCHeader, CQCCmdHeader, CQC_TP_COMMAND,\
    CQC_CMD_HDR_LENGTH, CQC_CMD_H, CQC_CMD_NEW, CQC_CMD_RELEASE

from utilities import get_header

from test_cases_cqcconnection.flush import (
    commands_to_apply_flush, get_expected_headers_flush
)


def get_expected_headers_simple_h():
    """What headers we expect"""
    hdr_tp_cmd = get_header(
        CQCHeader, 
        version=2,
        tp=CQC_TP_COMMAND,
        app_id=0,
        length=CQC_CMD_HDR_LENGTH,
    )
    hdr_cmd_new = get_header(
        CQCCmdHeader, 
        qubit_id=0,
        instr=CQC_CMD_NEW,
        notify=True,
        action=False,
        block=True,
    )
    hdr_cmd_h = get_header(
        CQCCmdHeader, 
        qubit_id=0,
        instr=CQC_CMD_H,
        notify=True,
        action=False,
        block=True,
    )
    hdr_cmd_release = get_header(
        CQCCmdHeader, 
        qubit_id=0,
        instr=CQC_CMD_RELEASE,
        notify=True,
        action=False,
        block=True,
    )

    expected_headers = [
        hdr_tp_cmd + hdr_cmd_new,
        hdr_tp_cmd + hdr_cmd_h,
        hdr_tp_cmd + hdr_cmd_release,
    ]

    return expected_headers


def commands_to_apply_simple_h(cqc):
    """What to do with the CQCConnection"""
    q = qubit(cqc)
    q.H()


@pytest.mark.parametrize("commands_to_apply, get_expected_headers", [
    (commands_to_apply_simple_h, get_expected_headers_simple_h),
    (commands_to_apply_flush, get_expected_headers_flush)
])
def test_commands(commands_to_apply, get_expected_headers, monkeypatch, mock_socket, mock_read_message):

    with CQCConnection("Test", socket_address=('localhost', 8000), use_classical_communication=False) as cqc:
        commands_to_apply(cqc)

    expected_headers = get_expected_headers()

    commands_sent = list(filter(lambda call: call.name == 'send', cqc._s.calls))
    assert len(expected_headers) == len(commands_sent)
    for command, expected in zip(commands_sent, expected_headers):
        print(command.args[0])
        print(expected)
        print()
        # Excluding None gives the opportunity to not specify all expected headers but still check the number of them
        if expected is not None:
            assert command.args[0] == expected
