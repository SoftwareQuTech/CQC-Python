import pytest

from cqc.pythonLib import CQCConnection, qubit, CQCMix
from cqc.cqcHeader import (
    Header,
    CQCCmdHeader,
    CQC_CMD_SEND,
    CQC_CMD_EPR,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_ROT_X,
    CQC_CMD_ROT_Y,
    CQC_CMD_ROT_Z,
    CQC_TP_HELLO,
    CQC_TP_COMMAND,
    CQC_TP_FACTORY,
    CQC_TP_GET_TIME,
    CQC_CMD_I,
    CQC_CMD_X,
    CQC_CMD_Y,
    CQC_CMD_Z,
    CQC_CMD_T,
    CQC_CMD_H,
    CQC_CMD_K,
    CQC_CMD_NEW,
    CQC_CMD_MEASURE,
    CQC_CMD_MEASURE_INPLACE,
    CQC_CMD_RESET,
    CQC_CMD_RECV,
    CQC_CMD_EPR_RECV,
    CQC_CMD_ALLOCATE,
    CQC_CMD_RELEASE,
    CQCCommunicationHeader,
    CQCXtraQubitHeader,
    CQCRotationHeader,
    CQC_VERSION,
    CQCHeader,
    CQC_TP_DONE,
    CQC_ERR_UNSUPP,
    CQC_ERR_UNKNOWN,
    CQC_ERR_GENERAL,
    CQCSequenceHeader,
    CQCFactoryHeader,
    CQC_TP_INF_TIME,
    CQC_ERR_NOQUBIT,
    CQCMeasOutHeader,
    CQCTimeinfoHeader,
    CQC_TP_MEASOUT,
    CQC_ERR_TIMEOUT,
    CQC_TP_RECV,
    CQC_TP_EPR_OK,
    CQC_TP_NEW_OK,
    CQC_TP_EXPIRE,
    CQCLogicalOperator,
    CQCIfHeader,
    CQCTypeHeader,
    CQCType,
    CQCAssignHeader
)

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
        hdr_tp_cmd,
        hdr_cmd_new,
        hdr_tp_cmd,
        hdr_cmd_h,
        hdr_tp_cmd + hdr_cmd_release,
    ]

    return expected_headers


def commands_to_apply_simple_h(cqc):
    """What to do with the CQCConnection"""
    q = qubit(cqc)
    q.H()


def commands_to_apply_bit_flip_code(cqc):
    qbit1 = qubit(cqc)
    qbit2 = qubit(cqc)
    qbit3 = qubit(cqc)

    with CQCMix(cqc) as pgrm:

        qbit1.cnot(qbit2)
        result1 = qbit2.measure(inplace=True)

        with pgrm.cqc_if(result1 == 1):
            qbit1.cnot(qbit3)
            result2 = qbit3.measure(inplace=True)

            with pgrm.cqc_if(result2 == 1):
                qbit1.X()

def get_expected_headers_bit_flip_code():

    cqc_header_tp_cmd = get_header(
        CQCHeader, 
        version=2,
        tp=CQCType.COMMAND,
        app_id=0,
        length=CQCCmdHeader.HDR_LENGTH
    )
    hdr_cmd_new = get_header(
        CQCCmdHeader, 
        qubit_id=0,
        instr=CQC_CMD_NEW,
        notify=True,
        action=False,
        block=True
    )

    return [
        cqc_header_tp_cmd,
        hdr_cmd_new,
        cqc_header_tp_cmd,
        hdr_cmd_new,
        cqc_header_tp_cmd,
        hdr_cmd_new,
        get_header(
            CQCHeader,
            version=2,
            tp=CQCType.MIX,
            app_id=0,
            length=95
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=6
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_CNOT,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCXtraQubitHeader, 
            qubit_id=2
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=8
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_MEASURE_INPLACE,
            notify=False,
            action=False,
            block=True,
        ),
        get_header(
            CQCAssignHeader, 
            ref_id=0
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=0, 
            operator=CQCLogicalOperator.EQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=1,
            length=52
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=6
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_CNOT,
            notify=True,
            action=False,
            block=True
        ),
        get_header(
            CQCXtraQubitHeader, 
            qubit_id=3
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=8
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=3,
            instr=CQC_CMD_MEASURE_INPLACE,
            notify=False,
            action=False,
            block=True
        ),
        get_header(
            CQCAssignHeader, 
            ref_id=1
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=1, 
            operator=CQCLogicalOperator.EQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=1,
            length=9
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_X,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH * 3
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=3,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
    ]


def commands_to_apply_simple_mix(cqc):
    qbit = qubit(cqc)

    with CQCMix(cqc) as pgrm:

        qbit.X()
        qbit.H()

def get_expected_headers_simple_mix():
    return [
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=0,
            instr=CQC_CMD_NEW,
            notify=True,
            action=False,
            block=True
        ),
        get_header(
            CQCHeader,
            version=2,
            tp=CQCType.MIX,
            app_id=0,
            length=18
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_X,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_H,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
    ]


def commands_to_apply_mix_with_factory(cqc):
    qbit = qubit(cqc)

    with CQCMix(cqc) as pgrm:
        qbit.X()
        
        with pgrm.loop(times=3):
            qbit.H()

        qbit.Y()

def get_expected_headers_mix_with_factory():
    return [
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=0,
            instr=CQC_CMD_NEW,
            notify=True,
            action=False,
            block=True
        ),
        get_header(
            CQCHeader,
            version=2,
            tp=CQCType.MIX,
            app_id=0,
            length=29
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_X,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.FACTORY,
            length=6
        ),
        get_header(
            CQCFactoryHeader,
            num_iter = 3
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_H,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_Y,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
    ]


def commands_to_apply_mix_if_else(cqc):
    qbit1 = qubit(cqc)
    qbit2 = qubit(cqc)

    with CQCMix(cqc) as pgrm:

        result = qbit1.measure(inplace=True)
        print(result.ref_id)

        with pgrm.cqc_if(result == 1):
            qbit2.X()

        with pgrm.cqc_else():
            qbit2.H()


def get_expected_headers_mix_if_else():
    cqc_header_tp_cmd = get_header(
        CQCHeader, 
        version=2,
        tp=CQCType.COMMAND,
        app_id=0,
        length=CQCCmdHeader.HDR_LENGTH
    )
    hdr_cmd_new = get_header(
        CQCCmdHeader, 
        qubit_id=0,
        instr=CQC_CMD_NEW,
        notify=True,
        action=False,
        block=True
    )

    return [
        cqc_header_tp_cmd,
        hdr_cmd_new,
        cqc_header_tp_cmd,
        hdr_cmd_new,
        get_header(
            CQCHeader,
            version=2,
            tp=CQCType.MIX,
            app_id=0,
            length=69
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=8
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_MEASURE_INPLACE,
            notify=False,
            action=False,
            block=True,
        ),
        get_header(
            CQCAssignHeader, 
            ref_id=0
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=0, 
            operator=CQCLogicalOperator.EQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=1,
            length=9
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_X,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=0, 
            operator=CQCLogicalOperator.NEQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=1,
            length=9
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_H,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH * 2
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
    ]


def commands_to_apply_mix_nested_if_else(cqc):
    qbit1 = qubit(cqc)
    qbit2 = qubit(cqc)
    qbit3 = qubit(cqc)

    with CQCMix(cqc) as pgrm:
        qbit1.H()
        result1 = qbit1.measure(inplace=True)

        with pgrm.cqc_if(result1 == 1):
            qbit2.H()
            result2 = qbit2.measure(inplace=True)

            with pgrm.cqc_if(result2 == 0):
                qbit3.X()
        with pgrm.cqc_else():
            qbit2.X()

def get_expected_headers_mix_nested_if_else():
    cqc_header_tp_cmd = get_header(
        CQCHeader, 
        version=2,
        tp=CQCType.COMMAND,
        app_id=0,
        length=CQCCmdHeader.HDR_LENGTH
    )
    hdr_cmd_new = get_header(
        CQCCmdHeader, 
        qubit_id=0,
        instr=CQC_CMD_NEW,
        notify=True,
        action=False,
        block=True
    )

    return [
        cqc_header_tp_cmd,
        hdr_cmd_new,
        cqc_header_tp_cmd,
        hdr_cmd_new,
        cqc_header_tp_cmd,
        hdr_cmd_new,
        get_header(
            CQCHeader,
            version=2,
            tp=CQCType.MIX,
            app_id=0,
            length=119
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_H,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=8
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_MEASURE_INPLACE,
            notify=False,
            action=False,
            block=True,
        ),
        get_header(
            CQCAssignHeader, 
            ref_id=0
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=0, 
            operator=CQCLogicalOperator.EQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=1,
            length=50
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_H,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=8
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_MEASURE_INPLACE,
            notify=False,
            action=False,
            block=True
        ),
        get_header(
            CQCAssignHeader, 
            ref_id=1
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=1, 
            operator=CQCLogicalOperator.EQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=0,
            length=9
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=3,
            instr=CQC_CMD_X,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.IF,
            length=14
        ),
        get_header(
            CQCIfHeader,
            first_operand=0, 
            operator=CQCLogicalOperator.NEQ,
            type_of_second_operand = CQCIfHeader.TYPE_VALUE, 
            second_operand=1,
            length=9
        ),
        get_header(
            CQCTypeHeader,
            tp=CQCType.COMMAND,
            length=4
        ),
        get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_X,
            notify=True,
            action=False,
            block=True,
        ),
        get_header(
            CQCHeader, 
            version=2,
            tp=CQCType.COMMAND,
            app_id=0,
            length=CQCCmdHeader.HDR_LENGTH * 3
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=1,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=2,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
        + get_header(
            CQCCmdHeader, 
            qubit_id=3,
            instr=CQC_CMD_RELEASE,
            notify=True,
            action=False,
            block=True,
        )
    ]



@pytest.mark.parametrize("commands_to_apply, get_expected_headers", [
    (commands_to_apply_simple_h, get_expected_headers_simple_h),
    (commands_to_apply_bit_flip_code, get_expected_headers_bit_flip_code),
    (commands_to_apply_simple_mix, get_expected_headers_simple_mix),
    (commands_to_apply_mix_with_factory, get_expected_headers_mix_with_factory),
    (commands_to_apply_mix_if_else, get_expected_headers_mix_if_else),
    (commands_to_apply_mix_nested_if_else, get_expected_headers_mix_nested_if_else),
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
