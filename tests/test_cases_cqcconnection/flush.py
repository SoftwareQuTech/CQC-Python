
from cqc.pythonLib import qubit
from cqc.cqcHeader import CQCHeader, CQCCmdHeader, CQC_TP_COMMAND,\
    CQC_CMD_HDR_LENGTH, CQC_CMD_H, CQC_CMD_NEW, CQC_CMD_RELEASE, \
    CQC_CMD_X

from utilities import get_header


def commands_to_apply_flush(cqc):
    """Test if CQCConnection automatically flushes when exiting context."""
    cqc.set_pending(True)
    assert cqc.pend_messages is True
    q = qubit(cqc)
    q.H()
    q.X()


def get_expected_headers_flush():
    """What headers we expect."""
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
    hdr_tp_cmd_2 = get_header(
        CQCHeader, 
        version=2,
        tp=CQC_TP_COMMAND,
        app_id=0,
        length=2 * CQC_CMD_HDR_LENGTH,
    )
    hdr_cmd_h = get_header(
        CQCCmdHeader, 
        qubit_id=1,
        instr=CQC_CMD_H,
        notify=True,
        action=False,
        block=True,
    )
    hdr_cmd_x = get_header(
        CQCCmdHeader,
        qubit_id=1,
        instr=CQC_CMD_X,
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
        hdr_tp_cmd_2,
        hdr_cmd_h,
        hdr_cmd_x,
        hdr_tp_cmd + hdr_cmd_release
    ]

    return expected_headers
