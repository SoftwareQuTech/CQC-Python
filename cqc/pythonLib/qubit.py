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
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
import warnings
from cqc.cqcHeader import (
    CQC_CMD_NEW,
    CQC_CMD_I,
    CQC_CMD_X,
    CQC_CMD_Y,
    CQC_CMD_Z,
    CQC_CMD_T,
    CQC_CMD_H,
    CQC_CMD_K,
    CQC_CMD_ROT_X,
    CQC_CMD_ROT_Y,
    CQC_CMD_ROT_Z,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_MEASURE,
    CQC_CMD_MEASURE_INPLACE,
    CQC_CMD_RESET,
    CQC_CMD_RELEASE,
)
from .util import (
    CQCGeneralError,
    CQCUnsuppError,
    QubitNotActiveError,
)


class qubit:
    """
    A qubit.
    """

    def __init__(self, cqc, notify=True, block=True, createNew=True, q_id=None, entInfo=None):
        """
        Initializes the qubit. The cqc connection must be given.
        If notify, the return message is received before the method finishes.
        createNew is set to False when we receive a qubit.

        - **Arguments**

            :cqc:         The CQCconnection used
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :createNew:     If NEW-message should be sent, used internally
            :q_id:         Qubit id, used internally if createNew
            :entInfo:     Entanglement information, if qubit is part of EPR-pair
        """
        # Cqc connection
        self._cqc = cqc

        self.notify = cqc.notify

        # Check if the cqc connection was openened using a 'with' statement
        # If not, raise a deprecation warning
        if not self._cqc._opened_with_with:
            logging.info(
                "You should open CQCConnection in a context, i.e. using 'with CQCConnection(...) as cqc:'. "
                "Then qubits will be automatically released by the end of the program, independently of what happens. "
                "For more information, see https://softwarequtech.github.io/SimulaQron/html/PythonLib.html"
            )

        # Whether the qubit is active. Will be set in the first run
        self._active = None

        if createNew:
            # print info
            logging.debug("App {} tells CQC: 'Create qubit'".format(self._cqc.name))

            # Create new qubit at the cqc server
            # TODO how to handle pending headers
            self._cqc.commit_command(0, CQC_CMD_NEW, notify=notify, block=block)
            
            # Get qubit id
            try:
                self._qID = self._cqc.new_qubitID()
            except AttributeError:
                raise CQCGeneralError("Didn't receive the qubit id")
            
            # Activate qubit
            self._set_active(True)
            if notify and self.notify:
                message = self._cqc.readMessage()
                self._cqc.print_CQC_msg(message)
        
        else:
            self._qID = q_id
            self._set_active(False)  # Why?

        # Entanglement information
        self._set_entanglement_info(entInfo)

    def __str__(self):
        if self.active:
            return "Qubit at the node {}".format(self._cqc.name)
        else:
            return "Not active qubit"

    @property
    def entanglement_info(self):
        return self._entInfo

    def _set_entanglement_info(self, ent_info):
        self._entInfo = ent_info

        # Lookup remote entangled node
        self._remote_entNode = None
        if self._entInfo:
            ip = self._entInfo.node_B
            port = self._entInfo.port_B
            try:
                for node in self._cqc._cqcNet.hostDict.values():
                    if (node.ip == ip) and (node.port == port):
                        self._remote_entNode = node.name
                        break
            except AttributeError:
                self._remote_entNode = None

    @property
    def active(self):
        return self._active

    @property
    def remote_entangled_node(self):
        return self._remote_entNode

    def get_entInfo(self):
        warnings.warn("get_entInfo is deprecated, use the property entanglement_info instead",
                      DeprecationWarning)
        return self._entInfo

    def print_entInfo(self):
        warnings.warn("print_entInfo is deprecated",
                      DeprecationWarning)
        if self.entanglement_info:
            print(self.entanglement_info)
        else:
            print("No entanglement information")

    def set_entInfo(self, entInfo):
        warnings.warn("set_entInfo is deprecated, use _set_entanglement_info instead",
                      DeprecationWarning)
        self._set_entanglement_info(entInfo)

    def is_entangled(self):
        if self._entInfo:
            return True
        return False

    def get_remote_entNode(self):
        warnings.warn("get_remote_entNode is deprecated, use the propery remote_entangled_node instead",
                      DeprecationWarning)
        return self.remote_entangled_node

    def check_active(self):
        """
        Checks if the qubit is active
        """
        if not self.active:
            raise QubitNotActiveError("Qubit is not active")

    def _set_active(self, be_active):

        # Check if not already new state
        if self._active == be_active:
            return

        if be_active:
            self._cqc.active_qubits.append(self)
        else:
            if self in self._cqc.active_qubits:
                self._cqc.active_qubits.remove(self)
        self._active = be_active

    def _single_qubit_gate(self, command, notify, block):
        """
        Performs a single qubit gate specified by the command, called in I(), X(), Y() etc
        :param command: the identifier of the command, as specified in cqcHeader.py
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        notify = notify and self.notify

        self._cqc.put_command(
            qID=self._qID,
            command=command,
            notify=notify,
            block=block,
        )

    def I(self, notify=True, block=True):
        """
        Performs an identity gate on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_I, notify, block)

    def X(self, notify=True, block=True):
        """
        Performs a X on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_X, notify, block)

    def Y(self, notify=True, block=True):
        """
        Performs a Y on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_Y, notify, block)

    def Z(self, notify=True, block=True):
        """
        Performs a Z on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_Z, notify, block)

    def T(self, notify=True, block=True):
        """
        Performs a T gate on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_T, notify, block)

    def H(self, notify=True, block=True):
        """
        Performs a Hadamard on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_H, notify, block)

    def K(self, notify=True, block=True):
        """
        Performs a K gate on the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_qubit_gate(CQC_CMD_K, notify, block)

    def _single_gate_rotation(self, command, step, notify, block):
        """
        Perform a rotation on a qubit
        :param command: the rotation qubit command as specified in cqcHeader.py
        :param step: Determines the rotation angle in steps of 2*pi/256
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        :return:
        """
        # check if qubit is active
        self.check_active()

        notify = notify and self.notify

        self._cqc.put_command(
            qID=self._qID,
            command=command,
            step=step,
            notify=notify,
            block=block,
        )

    def rot_X(self, step, notify=True, block=True):
        """
        Applies rotation around the x-axis with the angle of step*2*pi/256 radians.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :step:         Determines the rotation angle in steps of 2*pi/256
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_gate_rotation(CQC_CMD_ROT_X, step, notify, block)

    def rot_Y(self, step, notify=True, block=True):
        """
        Applies rotation around the y-axis with the angle of step*2*pi/256 radians.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :step:         Determines the rotation angle in steps of 2*pi/256
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_gate_rotation(CQC_CMD_ROT_Y, step, notify, block)

    def rot_Z(self, step, notify=True, block=True):
        """
        Applies rotation around the z-axis with the angle of step*2*pi/256 radians.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :step:         Determines the rotation angle in steps of 2*pi/256
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._single_gate_rotation(CQC_CMD_ROT_Z, step, notify, block)

    def _two_qubit_gate(self, command, target, notify, block):
        """
        Perform a two qubit gate on the qubit
        :param command: the two qubit gate command as specified in cqcHeader.py
        :param target: The target qubit
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()
        target.check_active()

        if self._cqc != target._cqc:
            raise CQCUnsuppError("Multi qubit operations can only operate on qubits in the same process")

        if self == target:
            raise CQCUnsuppError("Cannot perform multi qubit operation where control and target are the same")

        notify = notify and self.notify

        self._cqc.put_command(
            qID=self._qID,
            command=command,
            notify=notify,
            block=block,
            xtra_qID=target._qID,
        )

    def cnot(self, target, notify=True, block=True):
        """
        Applies a cnot onto target.
        Target should be a qubit-object with the same cqc connection.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :target:     The target qubit
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._two_qubit_gate(CQC_CMD_CNOT, target, notify, block)

    def cphase(self, target, notify=True, block=True):
        """
        Applies a cphase onto target.
        Target should be a qubit-object with the same cqc connection.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :target:     The target qubit
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        self._two_qubit_gate(CQC_CMD_CPHASE, target, notify, block)

    def measure(self, inplace=False, block=True):
        """
        Measures the qubit in the standard basis and returns the measurement outcome.
        If now MEASOUT message is received, None is returned.
        If inplace=False, the measurement is destructive and the qubit is removed from memory.
        If inplace=True, the qubit is left in the post-measurement state.

        - **Arguments**

            :inplace:     If false, measure destructively.
            :block:         Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        if inplace:
            command = CQC_CMD_MEASURE_INPLACE
        else:
            command = CQC_CMD_MEASURE
            # Set qubit to non active so the user can receive helpful errors during compile time 
            # if this qubit is used after this measurement
            self._set_active(False)

        self._cqc.put_command(
            qID=self._qID,
            command=command,
            notify=False,
            block=block,
        )

        if self._cqc.pend_messages:
            return None
        else:
            return self._cqc.return_meas_outcome()

    def reset(self, notify=True, block=True):
        """
        Resets the qubit.
        If notify, the return message is received before the method finishes.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        notify = notify and self.notify

        self._cqc.put_command(
            qID=self._qID,
            command=CQC_CMD_RESET,
            notify=notify,
            block=block,
        )

    def release(self, notify=True, block=True):
        """
        Release the current qubit
        :param notify: Do we wish to be notified when done
        :param block: Do we want the qubit to be blocked
        :return:
        """

        notify = notify and self.notify

        self._set_active(False)

        self._cqc.put_command(
            qID=self._qID,
            command=CQC_CMD_RELEASE,
            notify=notify,
            block=block,
        )

    def getTime(self, block=True):
        """
        Returns the time information of the qubit.
        If no INF_TIME message is received, None is returned.

        - **Arguments**

            :block:         Do we want the qubit to be blocked
        """
        # check if qubit is active
        self.check_active()

        # print info
        logging.debug("App {} tells CQC: 'Return time-info of qubit with ID {}'".format(self._cqc.name, self._qID))

        self._cqc.sendGetTime(self._qID, notify=0, block=int(block))

        # Return time-stamp
        message = self._cqc.readMessage()
        try:
            otherHdr = message[1]
            return otherHdr.datetime
        except AttributeError:
            return None
