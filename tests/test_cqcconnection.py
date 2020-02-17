import pytest

from cqc.util import parse_cqc_message
from cqc.pythonLib import CQCConnection, qubit
from cqc.pythonLib import CQCMixConnection
from cqc.cqcHeader import (
    CQCCmdHeader,
    CQCHeader,
    CQCType,
    CQC_CMD_H,
    CQC_CMD_NEW,
    CQC_CMD_RELEASE,
)

from utilities import get_header

from test_cases_cqcconnection.flush import (
    commands_to_apply_flush, get_expected_headers_flush
)

from test_cases_cqcconnection.cqc_mix import (
    commands_to_apply_bit_flip_code, 
    get_expected_headers_bit_flip_code,
    commands_to_apply_simple_mix, 
    get_expected_headers_simple_mix,
    commands_to_apply_mix_with_factory, 
    get_expected_headers_mix_with_factory,
    commands_to_apply_mix_if_else, 
    get_expected_headers_mix_if_else,
    commands_to_apply_mix_nested_if_else, 
    get_expected_headers_mix_nested_if_else,
)


def get_expected_headers_simple_h():
    """What headers we expect"""
    hdr_tp_cmd = get_header(
        CQCHeader, 
        version=2,
        tp=CQCType.COMMAND,
        app_id=0,
        length=CQCCmdHeader.HDR_LENGTH,
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
        qubit_id=1,
        instr=CQC_CMD_H,
        notify=True,
        action=False,
        block=True,
    )
    hdr_cmd_release = get_header(
        CQCCmdHeader, 
        qubit_id=1,
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


@pytest.mark.parametrize("conn_type, commands_to_apply, get_expected_headers", [
    (CQCConnection, commands_to_apply_simple_h, get_expected_headers_simple_h),
    (CQCConnection, commands_to_apply_flush, get_expected_headers_flush),
    (CQCMixConnection, commands_to_apply_bit_flip_code, get_expected_headers_bit_flip_code),
    (CQCMixConnection, commands_to_apply_simple_mix, get_expected_headers_simple_mix),
    (CQCMixConnection, commands_to_apply_mix_with_factory, get_expected_headers_mix_with_factory),
    (CQCMixConnection, commands_to_apply_mix_if_else, get_expected_headers_mix_if_else),
    (CQCMixConnection, commands_to_apply_mix_nested_if_else, get_expected_headers_mix_nested_if_else),
])
def test_commands(conn_type, commands_to_apply, get_expected_headers, monkeypatch, mock_socket, mock_read_message):
    # logging.getLogger().setLevel(logging.DEBUG)

    with conn_type("Test", socket_address=('localhost', 8000), use_classical_communication=False) as cqc:
        commands_to_apply(cqc)

    expected_messages = get_expected_headers()
    send_calls = list(filter(lambda call: call.name == 'send', cqc._s.calls))
    sent_messages = [call.args[0] for call in send_calls]

    full_msg = {}
    # Parse and print what we expect and what we got
    for name, messages in zip(["EXPECTED", "GOT"], [expected_messages, sent_messages]):
        print(f"\n{name}:")
        for msg in messages:
            print('[')
            for hdr in parse_cqc_message(msg):
                print(f"  {hdr}")
            print('\n]')
        full_msg[name] = b''.join([msg for msg in messages])

    # Check if full messages are equal
    assert full_msg["EXPECTED"] == full_msg["GOT"]
    for got, expected in zip(sent_messages, expected_messages):
        # Excluding None gives the opportunity to not specify all expected headers but still check the number of them
        if expected is not None:
            assert got == expected
