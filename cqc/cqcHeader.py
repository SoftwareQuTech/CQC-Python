#
# Copyright (c) 2017, Stephanie Wehner and Axel Dahlberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by Stephanie Wehner, QuTech.
# 4. Neither the name of the QuTech organization nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
# LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import warnings

import struct
import bitstring
import abc

from enum import IntEnum

# Constant defining CQC version
CQC_VERSION = 2

# !!!!!!!!! 
# Please do not use these header length constants. 
# Use the class static constants instead. For instance, use CQCCmdHeader.HDR_LENGTH instead of CQC_CMD_HDR_LENGTH
# !!!!!!!!!

# Lengths of the headers in bytes
CQC_HDR_LENGTH = 8  # Length of the CQC Header
CQC_CMD_HDR_LENGTH = 4  # Length of a command header
CQC_CMD_XTRA_LENGTH = 16  # Length of extra command information
CQC_SEQ_HDR_LENGTH = 1  # Length of the command sequence header
CQC_ROT_HDR_LENGTH = 1  # Length of the rotation header
CQC_XTRA_QUBIT_HDR_LENGTH = 2  # Length of the extra qubit header
CQC_COM_HDR_LENGTH = 8  # Length of the communication header
CQC_FACTORY_HDR_LENGTH = 2  # Length of the factory header
CQC_NOTIFY_LENGTH = 20  # Length of a notification send from the CQC upwards
CQC_MEAS_OUT_HDR_LENGTH = 1  # Length of the measurement outcome header
CQC_TIMEINFO_HDR_LENGTH = 8  # Length of the time info header
CQC_EPR_REQ_LENGTH = 16  # Length of EPR request header


# !!!!!!!!! 
# Please do not use these type constants. 
# Use the CQCType enum instead. For instance, use CQCType.HELLO instead of CQC_TP_HELLO
# !!!!!!!!!

# Constants defining the messages types
CQC_TP_HELLO = 0  # Alive check
CQC_TP_COMMAND = 1  # Execute a command list
CQC_TP_FACTORY = 2  # Start executing command list repeatedly
CQC_TP_EXPIRE = 3  # Qubit has expired
CQC_TP_DONE = 4  # Done with command
CQC_TP_RECV = 5  # Received qubit
CQC_TP_EPR_OK = 6  # Created EPR pair
CQC_TP_MEASOUT = 7  # Measurement outcome
CQC_TP_GET_TIME = 8  # Get creation time of qubit
CQC_TP_INF_TIME = 9  # Return timinig information
CQC_TP_NEW_OK = 10  # Created a new qubit

CQC_ERR_GENERAL = 20  # General purpose error (no details
CQC_ERR_NOQUBIT = 21  # No more qubits available
CQC_ERR_UNSUPP = 22  # No sequence not supported
CQC_ERR_TIMEOUT = 23  # Timeout
CQC_ERR_INUSE = 24  # Qubit already in use
CQC_ERR_UNKNOWN = 25  # Unknown qubit ID

# Possible commands
CQC_CMD_I = 0  # Identity (do nothing, wait one step)
CQC_CMD_NEW = 1  # Ask for a new qubit
CQC_CMD_MEASURE = 2  # Measure qubit
CQC_CMD_MEASURE_INPLACE = 3  # Measure qubit inplace
CQC_CMD_RESET = 4  # Reset qubit to |0>
CQC_CMD_SEND = 5  # Send qubit to another node
CQC_CMD_RECV = 6  # Ask to receive qubit
CQC_CMD_EPR = 7  # Create EPR pair with the specified node
CQC_CMD_EPR_RECV = 8  # Receive half of EPR pair created with other node

CQC_CMD_X = 10  # Pauli X
CQC_CMD_Z = 11  # Pauli Z
CQC_CMD_Y = 12  # Pauli Y
CQC_CMD_T = 13  # T Gate
CQC_CMD_ROT_X = 14  # Rotation over angle around X in 2pi/256 increments
CQC_CMD_ROT_Y = 15  # Rotation over angle around Y in 2pi/256 increments
CQC_CMD_ROT_Z = 16  # Rotation over angle around Z in 2pi/256 increments
CQC_CMD_H = 17  # Hadamard H
CQC_CMD_K = 18  # K Gate - taking computational to Y eigenbasis

CQC_CMD_CNOT = 20  # CNOT Gate with this as control
CQC_CMD_CPHASE = 21  # CPHASE Gate with this as control

CQC_CMD_ALLOCATE = 22  # Allocate a number of qubits
CQC_CMD_RELEASE = 23  # Release a qubit

# Command options
CQC_OPT_NOTIFY = 0x01  # Send a notification when cmd done
CQC_OPT_ACTION = 0x02  # On if there are actions to execute when done
CQC_OPT_BLOCK = 0x04  # Block until command is done

_CMD_TO_STRING = {
    CQC_CMD_I: "I",
    CQC_CMD_NEW: "NEW",
    CQC_CMD_MEASURE: "MEASURE",
    CQC_CMD_MEASURE_INPLACE: "MEASURE_INPLACE",
    CQC_CMD_RESET: "RESET",
    CQC_CMD_SEND: "SEND",
    CQC_CMD_RECV: "RECV",
    CQC_CMD_EPR: "EPR",
    CQC_CMD_EPR_RECV: "EPR_RECV",
    CQC_CMD_X: "X",
    CQC_CMD_Z: "Z",
    CQC_CMD_Y: "Y",
    CQC_CMD_T: "T",
    CQC_CMD_ROT_X: "ROT_X",
    CQC_CMD_ROT_Y: "ROT_Y",
    CQC_CMD_ROT_Z: "ROT_Z",
    CQC_CMD_H: "H",
    CQC_CMD_K: "K",
    CQC_CMD_CNOT: "CNOT",
    CQC_CMD_CPHASE: "CPHASE",
    CQC_CMD_ALLOCATE: "ALLOCATE",
    CQC_CMD_RELEASE: "RELEASE",
}


def command_to_string(cmd_id):
    cmd_str = _CMD_TO_STRING.get(cmd_id)
    if cmd_str is None:
        raise ValueError("Unknown instruction id {}".format(cmd_id))
    return cmd_str


class CQCType(IntEnum):
    HELLO = 0  # Alive check
    COMMAND = 1  # Execute a command list
    FACTORY = 2  # Start executing command list repeatedly
    EXPIRE = 3  # Qubit has expired
    DONE = 4  # Done with command
    RECV = 5  # Received qubit
    EPR_OK = 6  # Created EPR pair
    MEASOUT = 7  # Measurement outcome
    GET_TIME = 8  # Get creation time of qubit
    INF_TIME = 9  # Return timinig information
    NEW_OK = 10  # Created a new qubit
    MIX = 11  # Indicate that the CQC program will contain multiple header types
    IF = 12  # Announce a CQC IF header

    ERR_GENERAL = 20  # General purpose error (no details
    ERR_NOQUBIT = 21  # No more qubits available
    ERR_UNSUPP = 22  # No sequence not supported
    ERR_TIMEOUT = 23  # Timeout
    ERR_INUSE = 24  # Qubit already in use
    ERR_UNKNOWN = 25  # Unknown qubit ID


class CQCLogicalOperator(IntEnum):
    EQ = 0  # Equal
    NEQ = 1  # Not equal

    @staticmethod
    def opposite_of(operator: 'CQCLogicalOperator'):
        opposites = {
            CQCLogicalOperator.EQ: CQCLogicalOperator.NEQ,
            CQCLogicalOperator.NEQ: CQCLogicalOperator.EQ
        }
        return opposites[operator]

    @staticmethod
    def is_true(first_operand: int, operator: 'CQCLogicalOperator', second_operand: int):
        comparison_method = {
            CQCLogicalOperator.EQ: first_operand.__eq__,
            CQCLogicalOperator.NEQ: first_operand.__ne__
        }
        return comparison_method[operator](second_operand)


class Header(metaclass=abc.ABCMeta):
    """
    Abstact class for headers.
    Should be subclassed
    """
    
    PACKAGING_FORMAT = "!"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def __init__(self, headerBytes=None):
        """
            Initialize using values received from a packet.
            Don't override this but rather _setVals
        """
        if headerBytes is None:
            self.setVals()
            self.is_set = False
        else:
            self.unpack(headerBytes)

    def __str__(self):
        return self.printable()

    def setVals(self, *args, **kwargs):
        """
            Set using given values.
            Don't override this but rather _setVals

        :return: None
        """
        self._setVals(*args, **kwargs)
        self._check_vals()

    def _check_vals(self):
        """
            Method to be called after setting values, checks if values can be packed and sets is_set to True.

        :return: None
        """

        try:
            self.is_set = True
            self.pack()
        except Exception as err:
            # Set default values again
            raise ValueError("Invalid arguments. Could not packed since: {}".format(err))
            self.__init__()

    @abc.abstractmethod
    def _setVals(self, *args, **kwargs):
        """
            Set using given values.
            Should be overridden

        :return: None
        """
        pass

    def unpack(self, headerBytes):
        """
            Unpack packet data.
            Don't override this but rather _unpack

        :return: None
        """
        try:
            self._unpack(headerBytes)
        except Exception as err:
            raise ValueError("Could not unpack headerBytes={} to a {}, since {}"
                             .format(headerBytes, self.__class__.__name__, err))
        self.is_set = True

    @abc.abstractmethod
    def _unpack(self, headerBytes):
        """
            Unpack packet data.
            Should be overridden

        :return: None
        """
        pass

    def pack(self):
        """
            Pack data into packet format.
            Don't override this but rather _pack

        :return: bytes
        """
        if not self.is_set:
            raise RuntimeError("Cannot pack a header which is not set")
        return self._pack()

    @abc.abstractmethod
    def _pack(self):
        """
            Pack data into packet format.
            Should be overridden

        :return: bytes
        """
        pass

    def printable(self):
        """
            Produce a printable string for information purposes.
            Don't override this but rather _printable

        :return: str
        """
        if not self.is_set:
            raise RuntimeError("Cannot print a header which is not set")

        return self._printable()

    @abc.abstractmethod
    def _printable(self):
        """
            Produce a printable string for information purposes.
            Should be overridden

        :return: str
        """
        pass


class CQCHeader(Header):
    """
        Definition of the general CQC header.
    """

    PACKAGING_FORMAT = "!BBHL"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, version=0, tp=0, app_id=0, length=0):
        """
            Set using given values.
        """
        self.version = version
        self.tp = tp
        self.app_id = app_id
        self.length = length
        self.is_set = True

    def _pack(self):
        """
            Pack data into packet format. For defnitions see cLib/cgc.h
        """
        cqcH = struct.pack(self.PACKAGING_FORMAT, self.version, self.tp, self.app_id, self.length)
        return cqcH

    def _unpack(self, headerBytes):
        """
            Unpack packet data. For definitions see cLib/cqc.h
        """
        cqcH = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.version = cqcH[0]
        self.tp = cqcH[1]
        self.app_id = cqcH[2]
        self.length = cqcH[3]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "CQC Header. Version: " + str(self.version) + " "
        toPrint = toPrint + "Type: " + str(self.tp) + " "
        toPrint = toPrint + "App ID: " + str(self.app_id) + " "
        toPrint += "Length: " + str(self.length)
        return toPrint


class CQCTypeHeader(Header):
    """
        Definition of the CQC Type header. This header announces the type of the headers that will follow.
    """

    PACKAGING_FORMAT = "!BI"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)
    
    def _setVals(self, tp: CQCType = 0, length: int = 0) -> None:
        """
        Set using given values.
        """
        self.type = tp
        self.length = length

    def _pack(self) -> bytes:
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """
        return struct.pack(self.PACKAGING_FORMAT, self.type, self.length)
        
    def _unpack(self, headerBytes) -> None:
        """
        Unpack packet data.
        """
        unpacked = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.type = unpacked[0]
        self.length = unpacked[1]

    def _printable(self) -> str:
        """
        Produce a printable string for information purposes.
        """
        return "CQC Type header. Type=" + str(self.type) + " | Length=" + str(self.length)

    def make_equivalent_CQCHeader(self, version: int, app_id: int) -> CQCHeader:
        """
        Produce a CQC Header that is equivalent to this CQCTypeHeader. 
        This method does not make any modifications to self.
        """
        cqc_header = CQCHeader()
        cqc_header.setVals(version, self.type, app_id, self.length)
        return cqc_header
    

class CQCIfHeader(Header):
    """
        Definition of the CQC IF header.
    """

    PACKAGING_FORMAT = "!IBBII"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    TYPE_VALUE = 0
    TYPE_REF_ID = 1

    def _setVals(
        self, 
        first_operand: int = 0, 
        operator: CQCLogicalOperator = 0,
        type_of_second_operand: int = 0, 
        second_operand: int = 0,
        length: int = 0
    ) -> None:
        """
        Set the fields of this header. 
        first_operand must be a reference id.
        second_operand will be interpreted as eiter a reference id or a value, dependent on type_of_second_operand.
        type_of_second_operand must either be CQCIfHeader.TYPE_VALUE or CQCIfHeader.TYPE_REF_ID
        """

        self.first_operand = first_operand
        self.operator = operator
        self.type_of_second_operand = type_of_second_operand
        self.second_operand = second_operand
        self.length = length

    def _pack(self) -> bytes:
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """

        return struct.pack(
            self.PACKAGING_FORMAT, 
            self.first_operand, 
            self.operator, 
            self.type_of_second_operand, 
            self.second_operand, 
            self.length
        )     

    def _unpack(self, headerBytes) -> None:
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        unpacked = struct.unpack(self.PACKAGING_FORMAT, headerBytes)

        self.first_operand = unpacked[0]
        self.operator = unpacked[1]
        self.type_of_second_operand = unpacked[2]
        self.second_operand = unpacked[3]
        self.length = unpacked[4]

    def _printable(self) -> str:
        """
        Produce a printable string for information purposes.
        """
    
        if self.type_of_second_operand == self.TYPE_REF_ID:
            operand_type = "RefID"
        else:
            operand_type = "Value"

        # parenthesis to concatenate the string over multiple lines
        return (
            "CQC IF header. RefID=" + str(self.first_operand)
            + " | Operator=" + str(self.operator)
            + " | " + operand_type + "=" + str(self.second_operand)
            + " | Second_operand_type=" + operand_type
            + " | Body_length=" + str(self.length)
        )


class CQCCmdHeader(Header):
    """
        Header for a command instruction packet.
    """

    PACKAGING_FORMAT = "!HBB"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)
    
    def _setVals(self, qubit_id=0, instr=0, notify=False, block=False, action=False):
        """
        Set using given values.
        """
        self.qubit_id = qubit_id
        self.instr = instr
        self.notify = notify
        self.block = block
        self.action = action

    def _pack(self):
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """

        opt = 0
        if self.notify:
            opt = opt | CQC_OPT_NOTIFY
        if self.block:
            opt = opt | CQC_OPT_BLOCK
        if self.action:
            opt = opt | CQC_OPT_ACTION

        cmdH = struct.pack(self.PACKAGING_FORMAT, self.qubit_id, self.instr, opt)
        return cmdH

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        cmdH = struct.unpack(self.PACKAGING_FORMAT, headerBytes)

        self.qubit_id = cmdH[0]
        self.instr = cmdH[1]

        if cmdH[2] & CQC_OPT_NOTIFY:
            self.notify = True
        else:
            self.notify = False
        if cmdH[2] & CQC_OPT_BLOCK:
            self.block = True
        else:
            self.block = False
        if cmdH[2] & CQC_OPT_ACTION:
            self.action = True
        else:
            self.action = False

    def _printable(self):
        """
        Produce a printable string for information purposes.
        """
        toPrint = "Command Header. Qubit ID: " + str(self.qubit_id) + " "
        toPrint = toPrint + "Instruction: " + str(self.instr) + " "
        toPrint = toPrint + "Notify: " + str(self.notify) + " "
        toPrint = toPrint + "Block: " + str(self.block) + " "
        toPrint = toPrint + "Action: " + str(self.action)
        return toPrint


class CQCAssignHeader(Header):
    """
        Sub header that follows a CMD Measure header. It contains the reference id which can be used 
        to refer to the measurement outcome
    """

    PACKAGING_FORMAT = "!I"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, ref_id: int = 0) -> None:
        """
        Set using given values.
        """
        self.ref_id = ref_id

    def _pack(self) -> bytes:
        """
        Pack data into packet format. For defnitions see cLib/cgc.h
        """

        return struct.pack(self.PACKAGING_FORMAT, self.ref_id)

    def _unpack(self, headerBytes) -> None:
        """
        Unpack packet data. For definitions see cLib/cqc.h
        """
        unpacked = struct.unpack(self.PACKAGING_FORMAT, headerBytes)

        self.ref_id = unpacked[0]

    def _printable(self) -> str:
        """
        Produce a printable string for information purposes.
        """

        return "CQC Assign sub header. RefID=" + str(self.ref_id)


class CQCXtraHeader(Header):
    """
    Optional addtional cmd header information. Only relevant for certain commands.
    """

    PACKAGING_FORMAT = "!HHLLHBB"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    # Deprecated, split into multiple headers
    def __init__(self, headerBytes=None):
        """
        Initialize using values received from a packet.
        """
        warnings.warn("Xtra Header is deprecated, it is split into different headers", DeprecationWarning)
        super().__init__(headerBytes)

    def _setVals(self, xtra_qubit_id=0, step=0, remote_app_id=0, remote_node=0, remote_port=0, cmdLength=0):
        """
            Set using given values.
        """
        self.qubit_id = xtra_qubit_id
        self.step = step
        self.remote_app_id = remote_app_id
        self.remote_node = remote_node
        self.remote_port = remote_port
        self.cmdLength = cmdLength

    def _pack(self):
        """
            Pack data into packet form. For definitions see cLib/cqc.h
        """
        xtraH = struct.pack(
            self.PACKAGING_FORMAT,
            self.qubit_id,
            self.remote_app_id,
            self.remote_node,
            self.cmdLength,
            self.remote_port,
            self.step,
            0,
        )
        return xtraH

    def _unpack(self, headerBytes):
        """
            Unpack packet data. For defnitions see cLib/cqc.h
        """
        xtraH = struct.unpack(self.PACKAGING_FORMAT, headerBytes)

        self.qubit_id = xtraH[0]
        self.remote_app_id = xtraH[1]
        self.remote_node = xtraH[2]
        self.cmdLength = xtraH[3]
        self.remote_port = xtraH[4]
        self.step = xtraH[5]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """

        toPrint = "Xtra Qubit: " + str(self.qubit_id) + " "
        toPrint = toPrint + "Angle Step: " + str(self.step) + " "
        toPrint = toPrint + "Remote App ID: " + str(self.remote_app_id) + " "
        toPrint = toPrint + "Remote Node: " + str(self.remote_node) + " "
        toPrint = toPrint + "Remote Port: " + str(self.remote_port) + " "
        toPrint = toPrint + "Command Length: " + str(self.cmdLength)

        return toPrint


class CQCSequenceHeader(Header):
    """
        Header used to indicate size of a sequence.
        Currently exactly the same as CQCRotationHeaer.
        Seperate classes used clearity and for possible future adaptability. (Increase length for example)
    """

    PACKAGING_FORMAT = "!B"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, cmd_length=0):
        """
        Set header using given values
        :param cmd_length: The step size of the rotation
        """
        self.cmd_length = cmd_length

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        header = struct.pack(self.PACKAGING_FORMAT, self.cmd_length)
        return header

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        header = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.cmd_length = header[0]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Sequence header. "
        toPrint += "Command length: " + str(self.cmd_length) + " "

        return toPrint


class CQCRotationHeader(Header):
    """
        Header used to define the rotation angle of a gate
    """

    PACKAGING_FORMAT = "!B"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, step=0):
        """
        Set header using given values
        :param step: The step size of the rotation
        """
        self.step = step

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        header = struct.pack(self.PACKAGING_FORMAT, self.step)
        return header

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        header = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.step = header[0]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Rotation header. "
        toPrint += "step size: " + str(self.step) + " "

        return toPrint


class CQCXtraQubitHeader(Header):
    """
        Header used to send qubit of a secondary qubit for two qubit gates
    """

    PACKAGING_FORMAT = "!H"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, qubit_id=0):
        """
        Set header using given values
        :param qubit_id: The id of the secondary qubit
        """
        self.qubit_id = qubit_id

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        header = struct.pack(self.PACKAGING_FORMAT, self.qubit_id)
        return header

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        header = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.qubit_id = header[0]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Extra Qubit header. "
        toPrint += "qubit id: " + str(self.qubit_id) + " "

        return toPrint


class CQCCommunicationHeader(Header):
    """
        Header used to send information to which node to send information to.
        Used for example in Send and EPR commands
        This header has a size of 8
    """

    PACKAGING_FORMAT = "!HHL"
    PACKAGING_FORMAT_V1 = "!HLH"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)  # Both versions have the same size

    def __init__(self, headerBytes=None, cqc_version=CQC_VERSION):
        """
        Initialize from packet data
        :param headerBytes:  packet data
        """
        self._cqc_version = cqc_version
        super().__init__(headerBytes)

    def _setVals(self, remote_app_id=0, remote_node=0, remote_port=0):
        """
        Set header using given values
        :param remote_app_id: Application ID of remote host
        :param remote_node: IP of remote host in cqc network
        :param remote_port: port of remote hode in cqc network
        """
        self.remote_app_id = remote_app_id
        self.remote_port = remote_port
        self.remote_node = remote_node

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :param cqc_version: The CQC version to be used
        :returns the packed header
        """
        if self._cqc_version < 2:
            header = struct.pack(self.PACKAGING_FORMAT_V1, self.remote_app_id, self.remote_node, self.remote_port)
        else:
            header = struct.pack(self.PACKAGING_FORMAT, self.remote_app_id, self.remote_port, self.remote_node)
        return header

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For defnitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        :param cqc_version: The CQC version to be used
        """
        if self._cqc_version < 2:
            header = struct.unpack(self.PACKAGING_FORMAT_V1, headerBytes)
            self.remote_app_id = header[0]
            self.remote_node = header[1]
            self.remote_port = header[2]
        else:
            header = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
            self.remote_app_id = header[0]
            self.remote_port = header[1]
            self.remote_node = header[2]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Communication header. "
        toPrint += "Remote App ID: " + str(self.remote_app_id) + " "
        toPrint += "Remote Node: " + str(self.remote_node) + " "
        toPrint += "Remote Port: " + str(self.remote_port) + " "

        return toPrint


class CQCFactoryHeader(Header):
    """
    Header used to send factory information
    """

    # could maybe include the notify flag in num_iter?
    # That halfs the amount of possible num_iter from 256 to 128
    PACKAGING_FORMAT = "!BB"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, num_iter=0, notify=0, block=0):
        """
        Set using give values
        :param num_iter: The amount of iterations to this factory
        :param notify: 		True if the factory should send a done message back
        :param block:		True if all commands in this factory should be blocked
        """
        self.num_iter = num_iter
        self.notify = notify
        self.block = block

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        """
        opt = 0
        if self.notify:
            opt = opt | CQC_OPT_NOTIFY
        if self.block:
            opt = opt | CQC_OPT_BLOCK

        factH = struct.pack(self.PACKAGING_FORMAT, self.num_iter, opt)
        return factH

    def _unpack(self, headerBytes):
        """
            Unpack packet data. For defnitions see cLib/cqc.h
        """
        fact_hdr = struct.unpack(self.PACKAGING_FORMAT, headerBytes)

        self.notify = fact_hdr[1] & CQC_OPT_NOTIFY
        self.block = fact_hdr[1] & CQC_OPT_BLOCK

        self.num_iter = fact_hdr[0]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Factory Header. "
        toPrint += "Number of iterations: " + str(self.num_iter) + " "
        return toPrint


class CQCNotifyHeader(Header):
    """
        Header used to specify notification details.
    """

    PACKAGING_FORMAT = "!HHLQHBB"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def __init__(self, headerBytes=None):
        """
            Initialize from packet data.
        """
        warnings.warn("Notify Header is deprecated, it is split into CQCXtraQubitHeader, CQCMeasOutHeader, "
                      "CQCTimeInfoHeader", DeprecationWarning)
        super().__init__(headerBytes)

    def _setVals(self, qubit_id=0, outcome=0, remote_app_id=0, remote_node=0, remote_port=0, datetime=0):
        """
        Set using given values.
        """
        self.qubit_id = qubit_id
        self.outcome = outcome
        self.remote_app_id = remote_app_id
        self.remote_node = remote_node
        self.remote_port = remote_port
        self.datetime = datetime

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        """
        xtraH = struct.pack(
            self.PACKAGING_FORMAT,
            self.qubit_id,
            self.remote_app_id,
            self.remote_node,
            self.datetime,
            self.remote_port,
            self.outcome,
            0,
        )
        return xtraH

    def _unpack(self, headerBytes):
        """
            Unpack packet data. For defnitions see cLib/cqc.h
        """
        xtraH = struct.unpack(self.PACKAGING_FORMAT, headerBytes)

        self.qubit_id = xtraH[0]
        self.remote_app_id = xtraH[1]
        self.remote_node = xtraH[2]
        self.datetime = xtraH[3]
        self.remote_port = xtraH[4]
        self.outcome = xtraH[5]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Qubit ID: " + str(self.qubit_id) + " "
        toPrint = toPrint + "Outcome: " + str(self.outcome) + " "
        toPrint = toPrint + "Remote App ID: " + str(self.remote_app_id) + " "
        toPrint = toPrint + "Remote Node: " + str(self.remote_node) + " "
        toPrint = toPrint + "Remote Port: " + str(self.remote_port) + " "
        toPrint = toPrint + "Datetime: " + str(self.datetime)
        return toPrint


class CQCMeasOutHeader(Header):
    """
    Header used to send a measurement outcome.
    """

    PACKAGING_FORMAT = "!B"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, outcome=0):
        """
        Set header using given values
        :param meas_out: The measurement outcome
        """
        self.outcome = outcome

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        header = struct.pack(self.PACKAGING_FORMAT, self.outcome)
        return header

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        header = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.outcome = header[0]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Measurement Outcome header. "
        toPrint += "measurement outcome: " + str(self.outcome) + " "

        return toPrint


class CQCTimeinfoHeader(Header):
    """
    Header used to send timing information
    """

    PACKAGING_FORMAT = "!Q"
    HDR_LENGTH = struct.calcsize(PACKAGING_FORMAT)

    def _setVals(self, datetime=0):
        """
        Set header using given values
        :param datetime: The timestamp
        """
        self.datetime = datetime

    def _pack(self):
        """
        Pack data into packet form. For definitions see cLib/cqc.h
        :returns the packed header
        """
        header = struct.pack(self.PACKAGING_FORMAT, self.datetime)
        return header

    def _unpack(self, headerBytes):
        """
        Unpack packet data. For definitions see cLib/cqc.h
        :param headerBytes: The unpacked headers.
        """
        header = struct.unpack(self.PACKAGING_FORMAT, headerBytes)
        self.datetime = header[0]

    def _printable(self):
        """
            Produce a printable string for information purposes.
        """
        toPrint = "Time Info header. "
        toPrint += "timestamp: " + str(self.datetime) + " "

        return toPrint


class CQCEPRRequestHeader(Header):
    HDR_LENGTH = 16
    PACKAGING_FORMAT = (
        "uint:32=remote_ip, "
        "float:32=min_fidelity, "
        "float:32=max_time, "
        "uint:16=remote_port, "
        "uint:8=num_pairs, "
        "uint:4=priority, "
        "uint:1=store, "
        "uint:1=atomic, "
        "uint:1=measure_directly, "
        "uint:1=0"
    )

    def _setVals(self, remote_ip=0, remote_port=0, num_pairs=0, min_fidelity=0.0, max_time=0.0, priority=0, store=True,
                 atomic=False, measure_directly=False):
        """
        Stores required parameters of Entanglement Generation Protocol Request

        :param remote_ip: int
            IP of the other node we are attempting to generate entanglement with
        :param remote_port: int
            Port number of other node.
        :param num_pairs: int
            The number of entangled pairs we are trying to generate
        :param min_fidelity: float
            The minimum acceptable fidelity for the pairs we are generating
        :param max_time: float
            The maximum amount of time we are permitted to take when generating the pairs
        :param priority: obj
            Priority on the request
        :param store: bool
            Specifies whether entangled qubits should be stored within a storage qubit or left within the communication
            qubit
        :param measure_directly: bool
            Specifies whether to measure the communication qubit directly after the photon is emitted
        """
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.num_pairs = num_pairs
        self.min_fidelity = min_fidelity
        self.max_time = max_time
        self.priority = priority
        self.store = store
        self.atomic = atomic
        self.measure_directly = measure_directly

    def _pack(self):
        """
        Pack the data in packet form.
        :return: str
        """
        to_pack = {
            "remote_ip": self.remote_ip,
            "remote_port": self.remote_port,
            "min_fidelity": self.min_fidelity,
            "max_time": self.max_time,
            "num_pairs": self.num_pairs,
            "priority": self.priority,
            "store": self.store,
            "atomic": self.atomic,
            "measure_directly": self.measure_directly,
        }
        request_Bitstring = bitstring.pack(self.PACKAGING_FORMAT, **to_pack)
        requestH = request_Bitstring.tobytes()

        return requestH

    def _unpack(self, headerBytes):
        """
        Unpack data.
        :param headerBytes: str
        :return:
        """
        request_Bitstring = bitstring.BitString(headerBytes)
        request_fields = request_Bitstring.unpack(self.PACKAGING_FORMAT)
        self.remote_ip = request_fields[0]
        self.min_fidelity = request_fields[1]
        self.max_time = request_fields[2]
        self.remote_port = request_fields[3]
        self.num_pairs = request_fields[4]
        self.priority = request_fields[5]
        self.store = request_fields[6]
        self.atomic = request_fields[7]
        self.measure_directly = request_fields[8]

    def _printable(self):
        """
        Produce printable string for information purposes
        :return: str
        """
        to_print = "EPR Request Header."
        to_print += "Remote IP: {}".format(self.remote_ip)
        to_print += "Remote port: {}".format(self.remote_port)
        to_print += "Min Fidelity: {}".format(self.min_fidelity)
        to_print += "Max Time: {}".format(self.max_time)
        to_print += "Num Pairs: {}".format(self.num_pairs)
        to_print += "Priority: {}".format(self.priority)
        to_print += "Store: {}".format(self.store)
        to_print += "Atomic: {}".format(self.atomic)
        to_print += "Measure Directly: {}".format(self.measure_directly)

        return to_print
