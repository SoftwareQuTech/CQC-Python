# Copyright (c) 2017-2018, Stephanie Wehner and Axel Dahlberg
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
from collections import defaultdict
from abc import ABC, abstractmethod

from cqc.cqcHeader import (
    CQCCmdHeader,
    CQC_CMD_SEND,
    CQC_CMD_EPR,
    CQC_CMD_CNOT,
    CQC_CMD_CPHASE,
    CQC_CMD_ROT_X,
    CQC_CMD_ROT_Y,
    CQC_CMD_ROT_Z,
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
    CQCXtraHeader,
    CQC_VERSION,
    CQCHeader,
    CQC_TP_DONE,
    CQC_ERR_UNSUPP,
    CQC_ERR_UNKNOWN,
    CQC_ERR_GENERAL,
    CQCFactoryHeader,
    CQCType,
    CQCTypeHeader,
    CQCAssignHeader,
    CQCIfHeader,
    CQCLogicalOperator
)
from twisted.internet.defer import DeferredLock, inlineCallbacks


class UnknownQubitError(Exception):
    def __init__(self, message):
        super().__init__(message)


def has_extra(cmd):
    """
    Check whether this command includes an extra header with additional information.
    """
    if cmd.instr == CQC_CMD_SEND:
        return True
    if cmd.instr == CQC_CMD_EPR:
        return True
    if cmd.instr == CQC_CMD_CNOT:
        return True
    if cmd.instr == CQC_CMD_CPHASE:
        return True
    if cmd.instr == CQC_CMD_ROT_X:
        return True
    if cmd.instr == CQC_CMD_ROT_Y:
        return True
    if cmd.instr == CQC_CMD_ROT_Z:
        return True
    if cmd.action:
        return True

    return False


def is_error_message(message: bytes):

    # Only CQCHeaders can be error messages, so if the length does not correspond it is not an error message
    try:
        header = CQCHeader(message)
    # A ValueError is raised by Header.__init__ if the message cannot be read as a CQCHeader.
    # Since only CQCHeaders can contain errors, this means the message is not an error
    except ValueError:
        return False

    error_types = {
        CQCType.ERR_GENERAL,
        CQCType.ERR_INUSE,
        CQCType.ERR_NOQUBIT,
        CQCType.ERR_TIMEOUT,
        CQCType.ERR_UNKNOWN,
        CQCType.ERR_UNSUPP
    }

    if header.tp in error_types:
        return True
    else:
        return False


def print_error(error):
    logging.error("Uncaught twisted error found: {}".format(error))


######
# Abstract class. Classes that inherit this class define how to handle incoming cqc messages.
######

class CQCMessageHandler(ABC):
    _sequence_lock = DeferredLock()

    def __init__(self, factory):
        # Functions to invoke when receiving a CQC Header of a certain type
        self.messageHandlers = {
            CQCType.HELLO: self.handle_hello,
            CQCType.COMMAND: self.handle_command,
            CQCType.FACTORY: self.handle_factory,
            CQCType.GET_TIME: self.handle_time,
            CQCType.MIX: self.handle_mix,
            CQCType.IF: self.handle_conditional
        }

        # Functions to invoke when receiving a certain command
        self.commandHandlers = {
            CQC_CMD_I: self.cmd_i,
            CQC_CMD_X: self.cmd_x,
            CQC_CMD_Y: self.cmd_y,
            CQC_CMD_Z: self.cmd_z,
            CQC_CMD_T: self.cmd_t,
            CQC_CMD_H: self.cmd_h,
            CQC_CMD_K: self.cmd_k,
            CQC_CMD_ROT_X: self.cmd_rotx,
            CQC_CMD_ROT_Y: self.cmd_roty,
            CQC_CMD_ROT_Z: self.cmd_rotz,
            CQC_CMD_CNOT: self.cmd_cnot,
            CQC_CMD_CPHASE: self.cmd_cphase,
            CQC_CMD_MEASURE: self.cmd_measure,
            CQC_CMD_MEASURE_INPLACE: self.cmd_measure_inplace,
            CQC_CMD_RESET: self.cmd_reset,
            CQC_CMD_SEND: self.cmd_send,
            CQC_CMD_RECV: self.cmd_recv,
            CQC_CMD_EPR: self.cmd_epr,
            CQC_CMD_EPR_RECV: self.cmd_epr_recv,
            CQC_CMD_NEW: self.cmd_new,
            CQC_CMD_ALLOCATE: self.cmd_allocate,
            CQC_CMD_RELEASE: self.cmd_release,
        }

        # Convenience
        self.name = factory.name
        self.return_messages = defaultdict(list)  # Dictionary of all cqc messages to return per app_id

        # Dictionary that stores all reference ids and their values privately for each app_id.
        # Query/assign like this: self.references[app_id][ref_id]
        self.references = defaultdict(dict)

    @inlineCallbacks
    def handle_cqc_message(self, header, message, transport=None):
        """
        This calls the correct method to handle the cqcmessage, based on the type specified in the header
        """
        self.return_messages[header.app_id] = []
        if header.tp in self.messageHandlers:
            try:
                should_notify = yield self.messageHandlers[header.tp](header, message)
                
                if should_notify:
                    # Send a notification that we are done if successful
                    logging.debug("CQC %s: Command successful, sent done.", self.name)
                    self.return_messages[header.app_id].append(
                        self.create_return_message(header.app_id, CQC_TP_DONE, cqc_version=header.version))
            except UnknownQubitError:
                logging.error("CQC {}: Couldn't find qubit with given ID".format(self.name))
                self.return_messages[header.app_id].append(
                    self.create_return_message(header.app_id, CQC_ERR_UNKNOWN, cqc_version=header.version))
            except NotImplementedError:
                logging.error("CQC {}: Command not implemented yet".format(self.name))
                self.return_messages[header.app_id].append(
                    self.create_return_message(header.app_id, CQC_ERR_UNSUPP, cqc_version=header.version))
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when handling CQC message: {}".format(self.name, err)
                )
                self.return_messages[header.app_id].append(
                    self.create_return_message(header.app_id, CQC_ERR_GENERAL, cqc_version=header.version))
        else:
            logging.error("CQC %s: Could not find cqc type %d in handlers.", self.name, header.yp)
            self.return_messages[header.app_id].append(
                self.create_return_message(header.app_id, CQC_ERR_UNSUPP, cqc_version=header.version))

    def retrieve_return_messages(self, app_id):
        """Retrieve the return messages of a given app_id"""
        return self.return_messages[app_id]

    @staticmethod
    def create_return_message(app_id, msg_type, length=0, cqc_version=CQC_VERSION):
        """
        Creates a messaage that the protocol should send back
        :param app_id: the app_id to which the message should be send
        :param msg_type: the type of message to return
        :param length: the length of additional message
        :param cqc_version: The cqc version of the message
        :return: a new header message to be send back
        """
        hdr = CQCHeader()
        hdr.setVals(cqc_version, msg_type, app_id, length)
        return hdr.pack()

    @staticmethod
    def create_extra_header(cmd, cmd_data, cqc_version=CQC_VERSION):
        """
        Create the extra header (communication header, rotation header, etc) based on the command
        """
        if cqc_version < 1:
            if has_extra(cmd):
                cmd_length = CQCXtraHeader.HDR_LENGTH
                hdr = CQCXtraHeader(cmd_data[:cmd_length])
                return hdr
            else:
                return None

        instruction = cmd.instr
        if instruction == CQC_CMD_SEND or instruction == CQC_CMD_EPR:
            cmd_length = CQCCommunicationHeader.HDR_LENGTH
            hdr = CQCCommunicationHeader(cmd_data[:cmd_length], cqc_version=cqc_version)
        elif instruction == CQC_CMD_CNOT or instruction == CQC_CMD_CPHASE:
            cmd_length = CQCXtraQubitHeader.HDR_LENGTH
            hdr = CQCXtraQubitHeader(cmd_data[:cmd_length])
        elif instruction == CQC_CMD_ROT_X or instruction == CQC_CMD_ROT_Y or instruction == CQC_CMD_ROT_Z:
            cmd_length = CQCRotationHeader.HDR_LENGTH
            hdr = CQCRotationHeader(cmd_data[:cmd_length])
        elif instruction == CQC_CMD_MEASURE or instruction == CQC_CMD_MEASURE_INPLACE:
            cmd_length = CQCAssignHeader.HDR_LENGTH
            hdr = CQCAssignHeader(cmd_data[:cmd_length])
        else:
            return None
        return hdr

    @inlineCallbacks
    def handle_command(self, header, data):
        """
        Handle incoming command requests.
        """
        logging.debug("CQC %s: Command received", self.name)
        # Run the entire command list, incl. actions after completion which here we will do instantly
        try:
            success, should_notify = yield self._process_command(header, header.length, data)
        except Exception as err:
            print_error(err)
            return False
        return success and should_notify

    @inlineCallbacks
    def _process_command(self, cqc_header, length, data, is_locked=False):
        """
            Process the commands - called recursively to also process additional command lists.
        """
        cmd_data = data
        # Read in all the commands sent
        cur_length = 0
        should_notify = None
        while cur_length < length:
            cmd = CQCCmdHeader(cmd_data[cur_length: cur_length + CQCCmdHeader.HDR_LENGTH])
            logging.debug("CQC %s got command header %s", self.name, cmd.printable())

            newl = cur_length + cmd.HDR_LENGTH
            # Should we notify
            should_notify = should_notify or cmd.notify

            # Create the extra header if it exist
            try:
                xtra = self.create_extra_header(cmd, cmd_data[newl:], cqc_header.version)
            except IndexError:
                xtra = None
                logging.debug("CQC %s: Missing XTRA Header", self.name)

            if xtra is not None:
                newl += xtra.HDR_LENGTH
                logging.debug("CQC %s: Read XTRA Header: %s", self.name, xtra.printable())

            # Run this command
            logging.debug("CQC %s: Executing command: %s", self.name, cmd.printable())
            if cmd.instr not in self.commandHandlers:
                logging.debug("CQC {}: Unknown command {}".format(self.name, cmd.instr))
                msg = self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.version)
                self.return_messages[cqc_header.app_id].append(msg)
                return False, 0
            try:
                succ = yield self.commandHandlers[cmd.instr](cqc_header, cmd, xtra)
            except NotImplementedError:
                logging.error("CQC {}: Command not implemented yet".format(self.name))
                self.return_messages[cqc_header.app_id].append(
                    self.create_return_message(cqc_header.app_id, CQC_ERR_UNSUPP, cqc_version=cqc_header.verstion))
                return False, 0
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when process command {}: {}".format(
                        self.name, cmd.instr, err
                    )
                )
                msg = self.create_return_message(cqc_header.app_id, CQC_ERR_GENERAL, cqc_version=cqc_header.version)
                self.return_messages[cqc_header.app_id].append(msg)
                return False, 0
            
            if succ is False:  # only if it explicitly is false, if succ is None then we assume it went fine
                return False, 0

            cur_length = newl
        return True, should_notify

    @inlineCallbacks
    def handle_factory(self, header, data):
        fact_l = CQCFactoryHeader.HDR_LENGTH
        # Get factory header
        if len(data) < header.length:
            logging.debug("CQC %s: Missing header(s) in factory", self.name)
            self.return_messages[header.app_id].append(
                self.create_return_message(header.app_id, CQC_ERR_UNSUPP, cqc_version=header.version))
            return False
        fact_header = CQCFactoryHeader(data[:fact_l])
        num_iter = fact_header.num_iter
        # Perform operation multiple times
        succ = True
        should_notify = fact_header.notify
        block_factory = fact_header.block
        logging.debug("CQC %s: Performing factory command with %s iterations", self.name, num_iter)
        if block_factory:
            logging.debug("CQC %s: Acquire lock for factory", self.name)
            self._sequence_lock.acquire()

        for _ in range(num_iter):
            try:
                succ, _ = yield self._process_command(header, header.length - fact_l, data[fact_l:], block_factory)
                if succ is False:
                    return False
            except Exception as err:
                logging.error(
                    "CQC {}: Got the following unexpected error when processing factory: {}".format(self.name, err)
                )
                self.return_messages[header.app_id].append(
                    self.create_return_message(header.app_id, CQC_ERR_GENERAL, cqc_version=header.version))
                return False

        if block_factory:
            logging.debug("CQC %s: Releasing lock for factory", self.name)
            self._sequence_lock.release()

        return succ and should_notify

    @inlineCallbacks
    def handle_mix(self, header: CQCHeader, data: bytes):
        """
        Handler for messages of TP_MIX. Notice that header is the CQC Header, 
        and data is the complete body, excluding the CQC Header.
        """
        # Strategy for handling TP_MIX:
        # The first bit of data will be a CQCType header. We extract this header.
        # We extract from this first CQCType header the type of the following instructions, and we invoke the 
        # corresponding handler from self.messageHandlers. This handler expects as parameter "header" a CQCHeader. 
        # Therefore, we construct the CQCHeader that corresponds to the CQCType header 
        # (remember that the CQCType header is just a reduced CQCHeader),
        # and input that constructed CQCHeader as "header" parameter.
        # After this handler returns, we repeat until the end of the program.

        current_position = 0

        while current_position < header.length:

            # Extract CQCTypeHeader
            type_header = CQCTypeHeader(data[current_position : current_position + CQCTypeHeader.HDR_LENGTH])

            current_position += CQCTypeHeader.HDR_LENGTH

            # Create equivalent CQCHeader
            equiv_cqc_header = type_header.make_equivalent_CQCHeader(header.version, header.app_id)

            result = yield self.messageHandlers[type_header.type](equiv_cqc_header, data[current_position:])
            
            current_position += type_header.length

            if type_header.type == CQCType.IF:
                current_position += result

        # A TP_MIX should return the first error if there is an error message present, and otherwise return one TP_DONE
        # Notice the [:] syntax. This ensures the underlying list is updated, and not just the variable.

        return_message = None
        for message in self.return_messages[header.app_id]:
            if is_error_message(message):
                return_message = message
                break
        
        if return_message is None:
            return_message = self.create_return_message(header.app_id, CQCType.DONE, cqc_version=header.version)

        self.return_messages[header.app_id][:] = [return_message]

        # The other handlers from self.message_handlers return a bool that indicates whether 
        # self.handle_cqc_message should append a TP_DONE message. This handle_mix method does that itself 
        # if necessary so we just return nothing (None).

    def handle_conditional(self, header: CQCHeader, data: bytes):
        """
        Handler for messages of TP_IF. 
        """
        # Strategy for handling TP_IF:
        # We extract the CQCIfHeader from the data. We then extract all necessary variables from the header.
        # We then evaluate the conditional. If the conditional evaluates to FALSE, then we return the bodylength of
        # the IF. The mix handler will then skip this bodylength. 
        # If the conditional evaluates to True, then we return 0.

        if_header = CQCIfHeader(data[:CQCIfHeader.HDR_LENGTH])

        try:
            first_operand_value = self.references[header.app_id][if_header.first_operand]

            if if_header.type_of_second_operand is CQCIfHeader.TYPE_VALUE:
                second_operand_value = if_header.second_operand
            else:
                second_operand_value = self.references[header.app_id][if_header.second_operand]
        # If one of the above lookups in self.references fails because the queried reference IDs haven't 
        # been assigned earlier, a KeyError will be raised
        except KeyError:
            self.return_messages[header.app_id].append(
                self.create_return_message(header.app_id, CQC_ERR_GENERAL, cqc_version=header.version)
            )
            # Since the referenced IDs don't exist, we consider this IF-statement to evaluate to False.
            return if_header.length

        if CQCLogicalOperator.is_true(first_operand_value, if_header.operator, second_operand_value):
            return 0
        else:
            return if_header.length

    @abstractmethod
    def handle_hello(self, header, data):
        pass

    @abstractmethod
    def handle_time(self, header, data):
        pass

    @abstractmethod
    def cmd_i(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_x(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_y(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_z(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_t(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_h(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_k(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_rotx(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_roty(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_rotz(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_cnot(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_cphase(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_measure(self, cqc_header, cmd, xtra, inplace=False):
        pass

    @abstractmethod
    def cmd_measure_inplace(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_reset(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_send(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_recv(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_epr(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_epr_recv(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_new(self, cqc_header, cmd, xtra, return_q_id=False):
        pass

    @abstractmethod
    def cmd_allocate(self, cqc_header, cmd, xtra):
        pass

    @abstractmethod
    def cmd_release(self, cqc_header, cmd, xtra):
        pass
