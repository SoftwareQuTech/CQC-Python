# Tests for the CQCToFile class

# To get a temporary directory start the function with
#
# filename = os.path.join(str(tmpdir), 'CQC_File')
#
# with CQCToFile(file=filename) as cqc:

import os

from cqc.util import parse_cqc_message
from cqc.pythonLib import CQCToFile, qubit
from cqc.cqcHeader import (
    CQCType,
    CQC_CMD_NEW,
    CQC_CMD_H,
    CQC_CMD_X,
    CQC_CMD_RELEASE,
    CQCHeader,
    CQCCmdHeader
)


def test_name(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename) as cqc:
        assert cqc.name == filename


def test_sendSimple(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename, binary=False) as cqc:
        cqc.sendSimple(CQCType.HELLO)

    with open(filename) as f:
        lines = f.readlines()
            
    assert len(lines) == 1

    # Check that the first line is a header of hello type
    headers = parse_cqc_message(eval(lines[0][:-1]))
    assert len(headers) == 1
    hdr = headers[0]
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.HELLO


def test_createqubit(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename, binary=False) as cqc:
         
        qubit(cqc)

        # Read the files before cqc goes out of context and flushes
        with open(filename) as f:
            lines = f.readlines()
            
    assert len(lines) == 1

    # Check that the first line initialize a qubit
    headers = parse_cqc_message(eval(lines[0][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_NEW


def test_releasequbit(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename, binary=False) as cqc:
         
        qubit(cqc)

    with open(filename) as f:
        lines = f.readlines()
            
    assert len(lines) == 2

    # Check that the first line initialize a qubit
    headers = parse_cqc_message(eval(lines[0][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_NEW

    # Check that the second line releases the qubit
    headers = parse_cqc_message(eval(lines[1][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_RELEASE


def test_Hgate(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename, binary=False) as cqc:
         
        q = qubit(cqc)
        q.H()

    with open(filename) as f:
        lines = f.readlines()
       
    # Since pend_messages=False there should be three lines
    assert len(lines) == 3

    # Check that the first line initialize a qubit
    headers = parse_cqc_message(eval(lines[0][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_NEW

    # Check that the second line does H
    headers = parse_cqc_message(eval(lines[1][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_H

    # Check that the third line releases the qubit
    headers = parse_cqc_message(eval(lines[2][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_RELEASE


def test_some_combinations(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename) as cqc:
         
        q = cqc.createEPR("Alice")
        q.H()
        a = qubit(cqc)
        a.cnot(q)
        cqc.sendQubit(a, "Alice")

        c = cqc.recvQubit()
        d = cqc.recvEPR()
        c.H()
        d.H()
        c.cnot(d)


def test_flushing(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename, pend_messages=True) as cqc:
        
        assert not cqc._pending_headers

        q = qubit(cqc)
        q.H()
        q.X()
        q.Z()

        assert cqc._pending_headers

        cqc.flush()

        assert not cqc._pending_headers 


def test_qubitIDs(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename) as cqc:

        a = qubit(cqc)
        a.X()
        b = qubit(cqc)
        b.Z()
        c = qubit(cqc)
        c.H()

        assert a._qID == 0
        assert b._qID == 1
        assert c._qID == 2


def test_measurement(tmpdir):

    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename) as cqc:

        q = qubit(cqc)
        a = q.measure()
        assert a == 0


def test_flush_on_exit(tmpdir):
    filename = os.path.join(str(tmpdir), 'CQC_File')

    with CQCToFile(file=filename, pend_messages=True, binary=False) as cqc:

        q = qubit(cqc)
        q.H()
        q.X()

    with open(filename) as f:
        lines = f.readlines()

    # Since pend_messages=True we should only get two lines
    assert len(lines) == 2

    # Check that the first line initialize a qubit
    headers = parse_cqc_message(eval(lines[0][:-1]))
    assert len(headers) == 2
    hdr, cmd = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert isinstance(cmd, CQCCmdHeader)
    assert cmd.qubit_id == 0
    assert cmd.instr == CQC_CMD_NEW

    # Check that the second line applies H, X and releases
    headers = parse_cqc_message(eval(lines[1][:-1]))
    assert len(headers) == 4
    hdr, *cmds = headers
    assert isinstance(hdr, CQCHeader)
    assert hdr.tp == CQCType.COMMAND
    assert len(cmds) == 3
    for cmd in cmds:
        assert isinstance(cmd, CQCCmdHeader)
        assert cmd.qubit_id == 0
    assert cmds[0].instr == CQC_CMD_H
    assert cmds[1].instr == CQC_CMD_X
    assert cmds[2].instr == CQC_CMD_RELEASE
