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

import os

from cqc.cqcHeader import CQCCmdHeader, CQC_CMD_MEASURE, CQC_CMD_MEASURE_INPLACE
from .qubit import qubit
from .cqc_handler import CQCHandler


class CQCToFile(CQCHandler):
    """Handler to be used when writing the CQC commands to a file."""

    def __init__(self, name=None, file='CQC_File', pend_messages=False,
                 overwrite=False, binary=True):

        if name is None:
            name = file

        # Call init of CQCHandler
        super().__init__(file, pend_messages=pend_messages)

        self.next_qubitID = 0

        self.binary = binary

        self.file = file

        # Check if file exists
        if overwrite:
            # Remove file if we can overwrite
            try:
                os.remove(self.file)
            except FileNotFoundError:
                pass
        else:
            if not os.path.isfile(self.file):
                pass
            else:
                # Append number to filename if can't overwrite
                num = 0
                while True:
                    if os.path.isfile(self.file + str(num)):
                        num += 1
                    else:
                        self.file = self.file + str(num)
                        break 

        # Don't want notify when writing to file
        self.notify = False

    def commit(self, msg):
        """Write a message to file.

        Message is written as string or as bytes depending on 
        self.binary
        """

        if self.binary is True:
            with open(self.file, 'ab') as f:
                f.write(msg)
        else:
            with open(self.file, 'a') as f:      
                f.write(str(msg) + '\n')

    def _handle_create_qubits(self, num_qubits):
        qubits = []
        for _ in range(num_qubits):
            q = qubit(self, createNew=False)
            q._qID = self.new_qubitID()
            q._set_active(True)
            qubits.append(q)

        return qubits

    def new_qubitID(self, print_cqc=False):
        """Provice new qubit ID.
        
        For CQCToFile we simply increase the qubit ID by one for each
        new qubit.
        """

        qubitID = self.next_qubitID

        self.next_qubitID += 1

        return qubitID

    def get_remote_from_directory_or_address(self, name):
        # Only return fixed address and port for now
        return 0, 0

    def _handle_epr_response(self, notify):
        # Initialize the qubit
        q = qubit(self, createNew=False)

        entInfoHdr = None  # TODO: create function that returns some fake entanglement info
        q_id = self.new_qubitID()

        q._set_entanglement_info(entInfoHdr)
        q._qID = q_id

        # Activate and return qubit
        q._set_active(True)

        return q

    def return_meas_outcome(self):
        """Return measurement outcome."""

        return 0

    def readMessage(self):
        """For now returns nothing"""
        return None

    def _handle_factory_response(self, num_iter, response_amount, should_notify=False):
        """Handles the responses from a factory command and returns a list of results"""
        res = []
        # Loop over the pending_headers to determine the total length and set should_notify
        for header in self._pending_headers:

            # Check if the current header is a Command header. It can also be a sub header
            if isinstance(header, CQCCmdHeader):
                
                if self.shouldReturn(header.instr):
                    # Build artificial responses
                    if header.instr in (CQC_CMD_MEASURE, CQC_CMD_MEASURE_INPLACE):
                        res.append(self.return_meas_outcome())
                    # TODO entanglement information etc
                    else:
                        q = None
                        if num_iter != 1:
                            q._set_active(False)
                            q = qubit(self, createNew=False)
                        if q is None:
                            q = qubit(self, createNew=False)
                        q._qID = self.new_qubitID()
                        q._set_entanglement_info(None)
                        q._set_active(True)
                        res.append(q)

        return res
