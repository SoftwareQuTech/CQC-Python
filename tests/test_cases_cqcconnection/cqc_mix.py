from cqc.pythonLib import qubit, CQCMix
from utilities import get_header
from cqc.cqcHeader import (
    CQCCmdHeader,
    CQC_CMD_CNOT,
    CQC_CMD_X,
    CQC_CMD_Y,
    CQC_CMD_H,
    CQC_CMD_NEW,
    CQC_CMD_MEASURE_INPLACE,
    CQC_CMD_RELEASE,
    CQCXtraQubitHeader,
    CQCHeader,
    CQCFactoryHeader,
    CQCLogicalOperator,
    CQCIfHeader,
    CQCTypeHeader,
    CQCType,
    CQCAssignHeader
)


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
        cqc_header_tp_cmd + hdr_cmd_new,
        cqc_header_tp_cmd + hdr_cmd_new,
        cqc_header_tp_cmd + hdr_cmd_new,
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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

    with CQCMix(cqc):

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
        )
        + get_header(
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
        )
        + get_header(
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
            num_iter=3
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
        cqc_header_tp_cmd + hdr_cmd_new,
        cqc_header_tp_cmd + hdr_cmd_new,
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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
        cqc_header_tp_cmd + hdr_cmd_new,
        cqc_header_tp_cmd + hdr_cmd_new,
        cqc_header_tp_cmd + hdr_cmd_new,
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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
            type_of_second_operand=CQCIfHeader.TYPE_VALUE, 
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
