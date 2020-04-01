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

import abc
import math
import logging
import warnings
from typing import Any, List
from itertools import count

from cqc.cqcHeader import (
    CQC_VERSION,
    CQC_TP_COMMAND,
    CQC_TP_GET_TIME,
    CQC_TP_HELLO,
    CQC_TP_DONE,
    CQC_TP_NEW_OK,
    CQC_TP_RECV,
    CQC_TP_EPR_OK,
    CQC_TP_MEASOUT,
    CQC_TP_EXPIRE,
    CQC_TP_INF_TIME,
    CQC_ERR_GENERAL,
    CQC_ERR_NOQUBIT,
    CQC_ERR_UNSUPP,
    CQC_ERR_TIMEOUT,
    CQC_ERR_UNKNOWN,
    CQC_CMD_NEW,
    CQC_CMD_SEND,
    CQC_CMD_EPR,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_ROT_X,
    CQC_CMD_ROT_Y,
    CQC_CMD_ROT_Z,
    CQC_CMD_MEASURE,
    CQC_CMD_MEASURE_INPLACE,
    CQC_CMD_RECV,
    CQC_CMD_EPR_RECV,
    CQC_CMD_ALLOCATE,
    CQC_TP_FACTORY,
    Header,
    CQCHeader,
    CQCCmdHeader,
    CQCTypeHeader,
    CQCAssignHeader,
    CQCFactoryHeader,
    CQCRotationHeader,
    CQCXtraQubitHeader,
    CQCCommunicationHeader,
    CQCType,
)
from .util import (
    CQCUnsuppError,
    CQCGeneralError,
    CQCNoQubitError,
    CQCTimeoutError,
    CQCUnknownError,
    ProgressBar,
)
from .qubit import qubit


class CQCHandler(abc.ABC):
    """This class defines the things any CQCHandler must do.

    It is to be subclassed by the various actual classes that handle CQC, such
    as CQCConnection and CQCToFile.
    """

    _appIDs = {}

    def __init__(self, name, app_id=None, pend_messages=False, notify=True):

        self.name = name

        # This flag is used to check if CQCConnection is opened using a 'with' statement.
        # Otherwise an deprecation warning is printed when instantiating qubits.
        self._opened_with_with = False

        # Set an app ID
        self._appID = self._get_new_app_id(app_id)

        self.active_qubits = []

        # This is a sort of global notify
        self.notify = notify

        # All qubits active for this connection
        self.active_qubits = []

        # List of pended header objects waiting to be sent to the backend
        self._pending_headers = []  # ONLY cqc.cqcHeader.Header objects should be in this list

        # Bool that indicates whether we are in a factory and thus should pend commands
        self.pend_messages = pend_messages

        # Keep track of pending messages
        self._pending_headers = []

    @property
    def pend_messages(self):
        return self._pend_messages

    @pend_messages.setter
    def pend_messages(self, value):
        self.set_pending(value)

    def __str__(self):
        return "CQC handler for node '{}'".format(self.name)

    def _get_new_app_id(self, app_id):
        """Finds a new app ID if not specific"""
        name = self.name
        if name not in self._appIDs:
            self._appIDs[name] = []

        # Which appID
        if app_id is None:
            for app_id in count(0):
                if app_id not in self._appIDs[name]:
                    self._appIDs[name].append(app_id)
                    return app_id
        else:
            if app_id in self._appIDs[name]:
                raise ValueError("appID={} is already in use".format(app_id))
            self._appIDs[name].append(app_id)
            return app_id

    def __enter__(self):
        # This flag is used to check if CQCHandler is opened using a 
        # 'with' statement.
        # Otherwise an deprecation warning is printed when instantiating
        # qubits.
        self._opened_with_with = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # All qubits should now be released
        self.close(release_qubits=True)

    @abc.abstractmethod
    def new_qubitID(self, print_cqc=False):
        """Provide new qubit ID.
        
        This method must provide the new qubit ID. This qubit ID could 
        be given by the server you are communicating with, or it might
        simply be a number that increases by one every time the method
        is used. This will depend on the type of CQCHandler being used.
        """
        pass

    @abc.abstractmethod
    def _handle_create_qubits(self, num_qubits, notify):
        """Handles responses after allocating qubits and returns a list of qubits"""
        pass

    @abc.abstractmethod
    def return_meas_outcome(self):
        """Return measurement outcome."""
        pass

    @abc.abstractmethod
    def commit(self, msg):
        """Commit a message. 

        This can mean sending it to the backend or just writing to file.
        """
        pass

    @abc.abstractmethod
    def _handle_factory_response(self, num_iter, response_amount, should_notify=False):
        """Handles the responses from a factory command and returns a list of results"""
        pass

    @abc.abstractmethod
    def get_remote_from_directory_or_address(self, name, **kwargs):
        """Returns the remote address of a given node"""
        pass

    @abc.abstractmethod
    def _handle_epr_response(self, notify):
        """Waits for and handles the response message and returns a qubit object."""
        pass

    @abc.abstractmethod
    def readMessage(self):
        """Receive the whole message from cqc server.

        Returns (CQCHeader,None,None), (CQCHeader,CQCNotifyHeader,None) 
        or (CQCHeader,CQCNotifyHeader,EntInfoHeader) depending on the 
        type of message.
        """
        pass

    def get_appID(self):
        """Returns the application ID."""

        return self._appID

    def commit_command(self, qID, command, notify=1, block=1, action=0, 
                       xtra_qID=0, step=0, remote_appID=0, remote_node=0, 
                       remote_port=0, ref_id=0):
        """Construct and commit command."""

        headers = self.construct_command_headers(
            qID, command, notify=notify, block=block, action=action, 
            xtra_qID=xtra_qID, step=step, remote_appID=remote_appID, 
            remote_node=remote_node, remote_port=remote_port, ref_id=ref_id)
        self.commit_headers(headers)

    def commit_headers(self, headers):
        """Packs a list of headers and commits the message"""
        msg = b''
        for header in headers:
            msg += header.pack()
        self.commit(msg)

    def put_command(self, qID, command, read_notify=True, **kwargs):
        """Puts a new command to be executed.

        If self.pend_messages is set to True, the messages are kept until flushing,
        otherwise they are commited directly.

        Parameters
        ----------
        qID: int
            Id of the qubit to apply the command on
        command: int
            What command to be executed
        read_notify : bool
            Whether to listen to a notify message in this function or if this is handled
            elsewhere (e.g. createEPR)
        """
        headers = self.construct_command_headers(qID=qID, command=command, **kwargs)
        str_of_headers = "".join(["\t{}\n".format(header) for header in headers])
        if self.pend_messages:
            headers = self._update_headers_before_pending(headers)
            logging.debug("App {} pends a command with headers:\n{}".format(
                self.name,
                str_of_headers,
            ))
            self.pend_headers(headers)
        else:
            logging.debug("App {} sends a command with headers:\n{}".format(
                self.name,
                str_of_headers,
            ))
            self.commit_headers(headers)
            if read_notify:
                notify = kwargs.get("notify", True)
                if notify:
                    message = self.readMessage()
                    self._assert_done_message(message)
                    self.print_CQC_msg(message)

    def _update_headers_before_pending(self, headers):
        # Don't include the CQC Headers since this is a sequence
        return headers[1:]

    def _assert_done_message(self, message):
        if message[0].tp != CQC_TP_DONE:
            raise CQCUnsuppError(
                "Unexpected message sent back from the server. Message: {}".format(message[0])
            )

    def pend_headers(self, headers):
        """Pends the given headers"""
        for header in headers:
            self.pend_header(header)
    
    def pend_header(self, header: Header) -> None:
        self._pending_headers.append(header)

    def construct_command(self, qID, command, **kwargs):
        """Construct a commmand and packs it in it's binary form.

        Extra arguments are only used if the command if of a type that 
        needs them.

        - **Arguments**

            :qID:               qubit ID
            :command:           Command to be executed, eg CQC_CMD_H
            :nofify:            Do we wish to be notified when done.
            :block:             Do we want the qubit to be blocked
        """
        headers = self.construct_command_headers(qID, command, **kwargs)
        msg = b''
        for header in headers:
            msg += header.pack()
        return msg

    def construct_command_headers(self, qID, command, **kwargs):
        """Construct a commmand consisting of a list of header objects.

        Extra arguments are only used if the command if of a type that 
        needs them.

        - **Arguments**

            :qID:               qubit ID
            :command:           Command to be executed, eg CQC_CMD_H
            :nofify:            Do we wish to be notified when done.
            :block:             Do we want the qubit to be blocked
        """
        # Construct extra header if needed.
        xtra_hdr = None
        if command == CQC_CMD_SEND or command == CQC_CMD_EPR:
            xtra_hdr = CQCCommunicationHeader()
            remote_appID = kwargs.get("remote_appID", 0)
            remote_node = kwargs.get("remote_node", 0)
            remote_port = kwargs.get("remote_port", 0)
            xtra_hdr.setVals(remote_appID, remote_node, remote_port)
        elif command == CQC_CMD_CNOT or command == CQC_CMD_CPHASE:
            xtra_hdr = CQCXtraQubitHeader()
            xtra_qID = kwargs.get("xtra_qID", 0)
            xtra_hdr.setVals(xtra_qID)
        elif (command == CQC_CMD_ROT_X or command == CQC_CMD_ROT_Y 
              or command == CQC_CMD_ROT_Z):
            xtra_hdr = CQCRotationHeader()
            step = kwargs.get("step", 0)
            xtra_hdr.setVals(step)
        elif command == CQC_CMD_MEASURE or command == CQC_CMD_MEASURE_INPLACE:
            xtra_hdr = CQCAssignHeader()
            ref_id = kwargs.get("ref_id", 0)
            xtra_hdr.setVals(ref_id)

        # If xtra_hdr is None, we don't need an extra message.
        if xtra_hdr is None:
            header_length = CQCCmdHeader.HDR_LENGTH
        else:
            header_length = CQCCmdHeader.HDR_LENGTH + xtra_hdr.HDR_LENGTH

        # Construct Header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_COMMAND, self._appID, header_length)

        # Construct Command
        cmd_hdr = CQCCmdHeader()
        notify = int(kwargs.get("notify", True))
        block = int(kwargs.get("block", True))
        action = int(kwargs.get("action", False))
        cmd_hdr.setVals(qID, command, notify, block, action)

        headers = [hdr, cmd_hdr]
        if xtra_hdr is not None:
            headers.append(xtra_hdr)

        return headers

    def construct_simple(self, tp):
        """Construct simple message.
        
        For example a HELLO message if tp=CQC_TP_HELLO.
        """
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, tp, self._appID, 0)
        msg = hdr.pack()
        return msg

    def sendSimple(self, tp):
        """Construct and commit simple message."""
        msg = self.construct_simple(tp)
        self.commit(msg)

    def close(self, release_qubits=True):
        """Handle exiting of context."""

        if release_qubits:
            for q in list(self.active_qubits):
                q.release()

        # Flush all remaining commands and the releases
        self.flush()

        self._pop_app_id()

    def _pop_app_id(self):
        """
        Removes the used appID from the list.
        """
        try:
            self._appIDs[self.name].remove(self._appID)
        except ValueError:
            pass  # Already removed

    def create_qubits(self, num_qubits, block=True, notify=True):
        """Requests the backend to reserve some qubits

        :param num_qubits: The amount of qubits to reserve
        :return: A list of qubits
        :param notify:     Do we wish to be notified when done.
        :param block:         Do we want the qubit to be blocked
        """
        notify = self.notify and notify

        # TODO how to handle pending headers?
        headers = self.construct_command_headers(
            qID=num_qubits,
            command=CQC_CMD_ALLOCATE,
            notify=notify,
            block=block,
        )
        self.commit_headers(headers)

        qubits = self._handle_create_qubits(num_qubits=num_qubits, notify=notify)

        return qubits

    def sendGetTime(self, qID, notify=1, block=1, action=0):
        """Sends get-time message

        - **Arguments**

            :qID:         qubit ID
            :command:     Command to be executed, eg CQC_CMD_H
            :notify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :action:     Are there more commands to be executed
        """
        # Send Header
        hdr = CQCHeader()
        hdr.setVals(CQC_VERSION, CQC_TP_GET_TIME, self._appID, CQCCmdHeader.HDR_LENGTH)
        msg = hdr.pack()
        self.commit(msg)

        # Send Command
        cmd_hdr = CQCCmdHeader()
        cmd_hdr.setVals(qID, 0, notify, block, action)
        cmd_msg = cmd_hdr.pack()
        self.commit(cmd_msg)

    def allocate_qubits(self, nb_of_qubits: int) -> List['qubit']:
        """
        Creates (i.e. allocates) multiple qubits, and returns a list with qubit objects.

        :nb_of_qubits: The amount of qubits to be created.
        """
        warnings.warn("allocate_qubits is deprecated, use create_qubits instead",
                      DeprecationWarning)

        return self.create_qubits(nb_of_qubits)

    def createEPR(self, name, remote_appID=0, notify=True, block=True, **kwargs):
        """Creates epr with other host in the network.

        - **Arguments**

            :name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        remote_ip, remote_port = self.get_remote_from_directory_or_address(name, **kwargs)

        # print info
        logging.debug(
            "App {} puts message: 'Create EPR-pair with {} and appID {}'".format(self.name, name, remote_appID)
        )
        notify = self.notify and notify
        self.put_command(
            0,
            CQC_CMD_EPR,
            read_notify=False,
            notify=notify,
            block=block,
            remote_appID=remote_appID,
            remote_node=remote_ip,
            remote_port=remote_port,
        )
        if not self.pend_messages:
            q = self._handle_epr_response(notify=notify)
            return q

    def recvEPR(self, notify=True, block=True):
        """Receives a qubit from an EPR-pair generated with another node.

        - **Arguments**

            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        # print info
        logging.debug("App {} puts message: 'Receive half of EPR'".format(self.name))
        notify = self.notify and notify
        self.put_command(
            qID=0,
            command=CQC_CMD_EPR_RECV,
            read_notify=False,
            notify=notify,
            block=block,
        )

        if not self.pend_messages:
            q = self._handle_epr_response(notify=notify)
            return q

    def sendQubit(self, q, name, remote_appID=0, notify=True, block=True, **kwargs):
        """Sends qubit to another node in the cqc network. 
        
        If this node is not in the network an error is raised.

        - **Arguments**

            :q:         The qubit to send.
            :Name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """
        remote_ip, remote_port = self.get_remote_from_directory_or_address(name, **kwargs)

        # print info
        logging.debug(
            "App {} puts message: 'Send qubit with ID {} to {} and appID {}'".format(
                self.name, q._qID, name, remote_appID
            )
        )
        notify = self.notify and notify
        self.put_command(
            qID=q._qID,
            command=CQC_CMD_SEND,
            notify=notify, 
            block=block,
            remote_appID=remote_appID, 
            remote_node=remote_ip,
            remote_port=remote_port,
        )
        # Deactivate qubit
        # TODO should this be done if pending messages?
        q._set_active(False)

    def recvQubit(self, notify=True, block=True):
        """Receives a qubit.

        - **Arguments**

            :q:         The qubit to send.
            :Name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
        """

        # print info
        logging.debug("App {} puts message: 'Receive qubit'".format(self.name))
        notify = self.notify and notify
        self.put_command(0, CQC_CMD_RECV, read_notify=False, notify=notify, block=block)
        if not self.pend_messages:
            # Get qubit id
            q_id = self.new_qubitID(print_cqc=True)

            # initialize the qubit
            q = qubit(self, createNew=False)
            q._qID = q_id

            # Activate and return qubit
            q._set_active(True)

            # Read the notify message
            if notify:
                message = self.readMessage()
                self._assert_done_message(message)
                self.print_CQC_msg(message)

            return q

    def flush(self, do_sequence=False):
        """Flush all pending messages to the backend.
        
        :param do_sequence: boolean to indicate if you want to send the pending messages as a sequence
        :return: A list of things that are sent back from the server. Can be qubits, or outcomes
        """
        return self.flush_factory(1, do_sequence)

    def flush_factory(self, num_iter, do_sequence=False, block_factory=False):
        """
        Flushes the current pending sequence in a factory. It is performed multiple times
        :param num_iter: The amount of times the current pending sequence is performed
        :return: A list of outcomes/qubits that are produced by the commands
        """
        if len(self._pending_headers) == 0:
            return []

        # Initialize should_notify to False
        should_notify = False

        # Store how many of the headers we send will get a response message from the backend
        response_amount = 0

        # Loop over the pending_headers to determine the total length and set should_notify
        for header in self._pending_headers:

            # Check if the current header is a Command header. It can also be a sub header
            if isinstance(header, CQCCmdHeader):
                # set should_notify to True if at least one of all command headers has notify to True
                should_notify = should_notify or header.notify
                
                # Remember this header if we expect a return messge
                if self.shouldReturn(header.instr):
                    response_amount += 1

        # Determine the CQC Header type
        if num_iter == 1:
            cqc_type = CQC_TP_COMMAND
        else:
            # Build and insert the Factory header
            cqc_type = CQC_TP_FACTORY
            factory_header = CQCFactoryHeader()
            factory_header.setVals(num_iter, should_notify, block_factory)
            # Insert the factory header at the front
            self._pending_headers.insert(0, factory_header)
            
        # Insert the cqc header
        self.insert_cqc_header(cqc_type)
        
        # Send all pending headers
        self.send_pending_headers()

        # Reset _pending_headers to an empty list after all headers are sent
        self.reset_pending_headers()

        # Read out any returned messages from the backend
        res = self._handle_factory_response(num_iter, response_amount, should_notify=should_notify)
        
        # Return information that the backend returned
        return res

    def send_pending_headers(self) -> List[Any]:
        """
        Sends all pending headers.
        After sending, self._pending_headers is emptied.
        """

        # Send all pending headers
        to_log = "App {} sends a message with the following headers:\n".format(self.name)
        msg = b''
        for header in self._pending_headers:
            to_log += "\t{}\n".format(header)
            msg += header.pack()
        logging.debug(to_log[:-1])
        self.commit(msg)

    def reset_pending_headers(self):
        """Sets the list of pending headers to empty """
        self._pending_headers = []

    def set_pending(self, pend_messages):
        """Set the pend_messages flag.

        If true, flush() has to be called to send all self._pending_headers in sequence to the backend
        If false, all commands are directly send to the back_end
        :param pend_messages: Boolean to indicate if messages should pend or not
        """
        # Check if the list is not empty, give a warning if it isn't
        if self._pending_headers:
            logging.warning("List of pending headers is not empty, flushing them")
            self.flush()
        self._pend_messages = pend_messages

    def insert_cqc_header(self, cqc_type: CQCType, version=CQC_VERSION) -> None:
        """
        Inserts a CQC Header at index 0 of self._pending_headers.
        Invoke this method *after* all other headers are pended, so that the correct message length is calculated.
        """

        # Count the total message length
        message_length = 0
        for header in self._pending_headers:
            message_length += header.HDR_LENGTH

        # Build the CQC Header
        cqc_header = CQCHeader()
        cqc_header.setVals(CQC_VERSION, cqc_type, self._appID, message_length)

        # Insert CQC Header at the front
        self._pending_headers.insert(0, cqc_header)

    def _pend_type_header(self, cqc_type: CQCType, length: int) -> None:
        """
        Creates a CQCTypeHeader and pends it.
        """
        header = CQCTypeHeader()
        header.setVals(cqc_type, length)
        self.pend_header(header)

    def tomography(self, preparation, iterations, progress=True):
        """
        Does a tomography on the output from the preparation specified.
        The frequencies from X, Y and Z measurements are returned as a tuple (f_X,f_Y,f_Z).

        - **Arguments**

            :preparation:     A function that takes a CQCConnection as input and prepares a qubit and returns this
            :iterations:     Number of measurements in each basis.
            :progress_bar:     Displays a progress bar
        """
        accum_outcomes = [0, 0, 0]
        if progress:
            bar = ProgressBar(3 * iterations)

            # Measure in X
        for _ in range(iterations):
            # Progress bar
            if progress:
                bar.increase()

            # prepare and measure
            q = preparation(self)
            q.H()
            m = q.measure()
            accum_outcomes[0] += m

            # Measure in Y
        for _ in range(iterations):
            # Progress bar
            if progress:
                bar.increase()

            # prepare and measure
            q = preparation(self)
            q.K()
            m = q.measure()
            accum_outcomes[1] += m

            # Measure in Z
        for _ in range(iterations):
            # Progress bar
            if progress:
                bar.increase()

            # prepare and measure
            q = preparation(self)
            m = q.measure()
            accum_outcomes[2] += m

        if progress:
            bar.close()
            del bar

        freqs = map(lambda x: x / iterations, accum_outcomes)
        return list(freqs)

    def test_preparation(self, preparation, exp_values, conf=2, iterations=100, progress=True):
        """Test the preparation of a qubit.
        Returns True if the expected values are inside the confidence interval produced from the data received from
        the tomography function

        - **Arguments**

            :preparation:     A function that takes a CQCConnection as input and prepares a qubit and returns this
            :exp_values:     The expected values for measurements in the X, Y and Z basis.
            :conf:         Determines the confidence region (+/- conf/sqrt(iterations) )
            :iterations:     Number of measurements in each basis.
            :progress_bar:     Displays a progress bar
        """
        epsilon = conf / math.sqrt(iterations)

        freqs = self.tomography(preparation, iterations, progress=progress)
        for i in range(3):
            if abs(freqs[i] - exp_values[i]) > epsilon:
                print(freqs, exp_values, epsilon)
                return False
        return True

    def print_CQC_msg(self, message):
        """
        Prints messsage returned by the readMessage method of CQCConnection.
        """
        # First check if there was an error
        self.check_error(message[0])

        hdr = message[0]
        otherHdr = message[1]
        entInfoHdr = message[2]

        if hdr.tp == CQC_TP_HELLO:
            logging.debug("CQC tells App {}: 'HELLO'".format(self.name))
        elif hdr.tp == CQC_TP_EXPIRE:
            logging.debug("CQC tells App {}: 'Qubit with ID {} has expired'".format(self.name, otherHdr.qubit_id))
        elif hdr.tp == CQC_TP_DONE:
            logging.debug("CQC tells App {}: 'Done with command'".format(self.name))
        elif hdr.tp == CQC_TP_RECV:
            logging.debug("CQC tells App {}: 'Received qubit with ID {}'".format(self.name, otherHdr.qubit_id))
        elif hdr.tp == CQC_TP_EPR_OK:

            # Lookup host name
            remote_node = entInfoHdr.node_B
            remote_port = entInfoHdr.port_B
            remote_name = None
            try:
                for node in self._cqcNet.hostDict.values():
                    if (node.ip == remote_node) and (node.port == remote_port):
                        remote_name = node.name
                        break
                if remote_name is None:
                    raise RuntimeError("Remote node ({},{}) is not in config-file.".format(remote_node, remote_port))
            except AttributeError:
                remote_name = "({}, {})".format(remote_node, remote_port)

            logging.debug(
                "CQC tells App {}: 'EPR created with node {}, using qubit with ID {}'".format(
                    self.name, remote_name, otherHdr.qubit_id
                )
            )
        elif hdr.tp == CQC_TP_MEASOUT:
            logging.debug("CQC tells App {}: 'Measurement outcome is {}'".format(self.name, otherHdr.outcome))
        elif hdr.tp == CQC_TP_INF_TIME:
            logging.debug("CQC tells App {}: 'Timestamp is {}'".format(self.name, otherHdr.datetime))

    def parse_CQC_msg(self, message, q=None, is_factory=False):
        """
        parses the cqc message and returns the relevant value of that measure
        (qubit, measurement outcome)

        :param message: str
            the cqc message to be parsed
        :param q: :obj:`cqc.pythonLib.qubit`
            the qubit object we should save the qubit to
        :param is_factory: bool
            whether the returned message came from a factory. If so, do not change the qubit, but create a new one
        :return: the result of the message (either a qubit, or a measurement outcome. Otherwise None
        """
        hdr = message[0]
        otherHdr = message[1]
        if len(message) < 3:
            entInfoHdr = None
        else:
            entInfoHdr = message[2]

        if hdr.tp in {CQC_TP_RECV, CQC_TP_NEW_OK, CQC_TP_EPR_OK}:
            if is_factory:
                q._set_active(False)  # Set qubit to inactive so it can't be used anymore
                q = qubit(self, createNew=False)
            if q is None:
                q = qubit(self, createNew=False)
            q._qID = otherHdr.qubit_id
            q._set_entanglement_info(entInfoHdr)
            q._set_active(True)
            return q
        if hdr.tp == CQC_TP_MEASOUT:
            return otherHdr.outcome
        if hdr.tp == CQC_TP_INF_TIME:
            return otherHdr.datetime

    def check_error(self, hdr):
        """Checks if there is an error returned."""

        self._errorHandler(hdr.tp)

    def _errorHandler(self, cqc_err):
        """Raises an error if there is an error-message."""

        if cqc_err == CQC_ERR_GENERAL:
            raise CQCGeneralError("General error")
        if cqc_err == CQC_ERR_NOQUBIT:
            raise CQCNoQubitError("No more qubits available")
        if cqc_err == CQC_ERR_UNSUPP:
            raise CQCUnsuppError("Sequence not supported")
        if cqc_err == CQC_ERR_TIMEOUT:
            raise CQCTimeoutError("Timeout")
        if cqc_err == CQC_ERR_UNKNOWN:
            raise CQCUnknownError("Unknown qubit ID")

    @staticmethod
    def shouldReturn(command):
        return command in {
            CQC_CMD_NEW,
            CQC_CMD_MEASURE,
            CQC_CMD_MEASURE_INPLACE,
            CQC_CMD_RECV,
            CQC_CMD_EPR_RECV,
            CQC_CMD_EPR,
        }

    @staticmethod
    def hasXtraHeader(command):
        return command in {
            CQC_CMD_CNOT,
            CQC_CMD_SEND,
            CQC_CMD_EPR,
            CQC_CMD_ROT_X,
            CQC_CMD_ROT_Y,
            CQC_CMD_ROT_Z,
            CQC_CMD_CPHASE,
        }
