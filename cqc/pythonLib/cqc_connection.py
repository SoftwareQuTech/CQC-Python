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

import time
import socket
import logging

from cqc.cqcHeader import (
    CQC_TP_NEW_OK,
    CQC_TP_RECV,
    CQC_TP_EPR_OK,
    CQC_TP_MEASOUT,
    CQC_TP_EXPIRE,
    CQC_TP_INF_TIME,
    Header,
    CQCHeader,
    CQCMeasOutHeader,
    CQCTimeinfoHeader,
    CQCXtraQubitHeader,
)
from cqc.entInfoHeader import EntInfoHeader
from cqc.hostConfig import cqc_node_id_from_addrinfo
from .cqc_handler import CQCHandler
from .util import CQCUnsuppError
from .qubit import qubit

try:
    import simulaqron
    from simulaqron.general.hostConfig import socketsConfig
    from simulaqron.settings import simulaqron_settings
    _simulaqron_version = simulaqron.__version__
    _simulaqron_major = int(_simulaqron_version.split('.')[0])
except ImportError:
    _simulaqron_major = -1


class CQCConnection(CQCHandler):
    """Handler to be used when sending commands over a socket."""
    def __init__(self, name, socket_address=None, appID=None, pend_messages=False,
                 retry_connection=True, conn_retry_time=0.1, log_level=None, backend=None,
                 use_classical_communication=True, network_name=None):
        """
        Initialize a connection to the cqc server.

        Since version 3.0.0: If socket_address is None or use_classical_communication is True, the CQC connection
        needs some way of finding the correct socket addresses. If backend is None or "simulaqron" the connection
        will try to make use of the network config file setup in simulaqron. If simulaqron is not installed

        - **Arguments**
            :param name:        Name of the host.
            :param socket_address: tuple (str, int) of ip and port number.
            :param appID:        Application ID. If set to None, defaults to a nonused ID.
            :param pend_messages: True if you want to wait with sending messages to the back end.
                    Use flush() to send all pending messages in one go as a sequence to the server
            :param retry_connection: bool
                Whether to retry a failed connection or not
            :param conn_retry_time: float
                How many seconds to wait between each connection retry
            :param log_level: int or None
                The log-level, for example logging.DEBUG (default: logging.WARNING)
            :param backend: None or str
                If socket_address is None or use_classical_communication is True, If None or "simulaqron" is used
                the cqc library tries to use the network config file setup in simulaqron if network_config_file is None.
                If network_config_file is None and simulaqron is not installed a ValueError is raised.
            :param use_classical_communication: bool
                Whether to use the built-in classical communication or not.
            :param network_name: None or str
                Used if simulaqron is used to load socket addresses for the backend
        """

        super().__init__(
            name=name,
            app_id=appID,
            pend_messages=pend_messages,
        )

        self._setup_logging(log_level)

        # Connection retry time
        self._conn_retry_time = conn_retry_time

        # Buffer received data
        self.buf = None

        # ClassicalServer
        self._classicalServer = None

        # Classical connections in the application network
        self._classicalConn = {}

        # Get network configuraton and addresses
        addr, cqc_net, app_net = self._setup_network_data(
            socket_address=socket_address,
            use_classical_communication=use_classical_communication,
            backend=backend,
            network_name=network_name,
        )
        self._cqcNet = cqc_net
        self._appNet = app_net

        # Open a socket to the backend
        self._s = None
        cqc_socket = self._setup_socket(addr=addr, retry_connection=retry_connection)
        self._s = cqc_socket

    @staticmethod
    def _setup_logging(level):
        """
        Sets up the logging to the specified level (default logging.WARNING)
        :param level: int or None
            For example logging.DEBUG
        :return: None
        """
        if level is None:
            logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=logging.WARNING)
        else:
            logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s", level=level)

    def _setup_network_data(self, socket_address, use_classical_communication, backend,
                            network_name):
        addr = None
        cqc_net = None
        app_net = None
        if socket_address is None or use_classical_communication:
            cqc_net, app_net = self._get_net_configs(
                use_classical_communication=use_classical_communication,
                backend=backend,
                network_name=network_name,
            )

            # Host data
            if self.name in cqc_net.hostDict:
                myHost = cqc_net.hostDict[self.name]
            else:
                raise ValueError("Host name '{}' is not in the cqc network".format(self.name))

                # Get IP and port number
            addr = myHost.addr

        if socket_address is not None:
            try:
                hostname, port = socket_address
                if not isinstance(hostname, str):
                    raise TypeError()
                if not isinstance(port, int):
                    raise TypeError()
                addrs = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
                addr = addrs[0]

            except Exception:
                raise TypeError("When specifying the socket address, this should be a tuple (str,int).")
        return addr, cqc_net, app_net

    def _get_net_configs(self, use_classical_communication, backend, network_name):
        cqc_net = None
        app_net = None
        if backend is None or backend == "simulaqron":
            if _simulaqron_major < 3:
                raise ValueError("If (socket_address is None or use_classical_communication is True)"
                                 "and (backend is None or 'simulaqron'\n"
                                 "you need simulaqron>=3.0.0 installed.")
            else:
                network_config_file = simulaqron_settings.network_config_file
                cqc_net = socketsConfig(network_config_file, network_name=network_name, config_type="cqc")
                if use_classical_communication:
                    app_net = socketsConfig(network_config_file, network_name=network_name, config_type="app")
        else:
            raise ValueError("Unknown backend")

        return cqc_net, app_net

    def _setup_socket(self, addr, retry_connection):
        cqc_socket = None
        while True:
            try:
                logging.debug("App {} : Trying to connect to CQC server".format(self.name))

                cqc_socket = socket.socket(addr[0], addr[1], addr[2])
                cqc_socket.connect(addr[4])
                break
            except ConnectionRefusedError as err:
                logging.debug("App {} : Could not connect to  CQC server, trying again...".format(self.name))
                time.sleep(self._conn_retry_time)
                cqc_socket.close()
                if not retry_connection:
                    self.close()
                    raise err
            except Exception as err:
                logging.exception("App {} : Critical error when connection to CQC server: {}".format(self.name, err))
                cqc_socket.close()
                raise err
        return cqc_socket

    def commit(self, msg):
        """Send message through the socket."""
        self._s.send(msg)

    def close(self, release_qubits=True, notify=True):
        """Handle closing actions.

        Flushes remaining headers, releases all qubits, closes the 
        connections, and removes the app ID from the used app IDs.
        """
        super().close()

        if self._s is not None:
            self._s.close()

        self.closeClassicalServer()

        for name in list(self._classicalConn):
            self.closeClassicalChannel(name)

    def new_qubitID(self, print_cqc=False):
        """Provide new qubit ID.
        
        For CQCConnection the qubit ID is given by the server. A message
        has to be read and the qubit ID extracted from it.
        """

        msg = self.readMessage()
        otherHdr = msg[1]

        if print_cqc:
            self.print_CQC_msg(msg)

        return otherHdr.qubit_id

    def startClassicalServer(self):
        """Sets up a server for the application communication, 
        if not already set up.
        """
        if self._appNet is None:
            raise ValueError(
                "Since use_classical_communication was set to False upon init, the built-in classical communication"
                "cannot be used."
            )

        if not self._classicalServer:
            logging.debug("App {}: Starting classical server".format(self.name))
            # Get host data
            myHost = self._appNet.hostDict[self.name]
            hostaddr = myHost.addr

            # Setup server
            s = socket.socket(hostaddr[0], hostaddr[1], hostaddr[2])
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(hostaddr[4])
            s.listen(1)
            (conn, addr) = s.accept()
            logging.debug("App {}: Classical server started".format(self.name))
            self._classicalServer = conn

    def closeClassicalServer(self):
        """Closes classical server."""

        if self._classicalServer:
            logging.debug("App {}: Closing classical server".format(self.name))
            self._classicalServer.close()
            logging.debug("App {}: Classical server closed".format(self.name))
            self._classicalServer = None

    def recvClassical(self, timout=1, msg_size=1024, close_after=True):
        """Receive classical message."""

        if not self._classicalServer:
            self.startClassicalServer()
        for _ in range(10 * timout):
            logging.debug("App {}: Trying to receive classical message".format(self.name))
            msg = self._classicalServer.recv(msg_size)
            if len(msg) > 0:
                logging.debug("App {}: Received classical message".format(self.name))
                if close_after:
                    self.closeClassicalServer()
                return msg
            time.sleep(0.1)
        raise RuntimeError("Timeout: No message received")

    def openClassicalChannel(self, name):
        """
        Opens a classical connection to another host in the application network.

        - **Arguments**

            :name:        The name of the host in the application network.
            :timout:    The time to try to connect to the server. When timout is reached an RuntimeError is raised.
        """
        if self._appNet is None:
            raise ValueError(
                "Since use_classical_communication was set to False upon init, the built-in classical communication"
                "cannot be used."
            )
        if name not in self._classicalConn:
            logging.debug("App {}: Opening classical channel to {}".format(self.name, name))
            if name in self._appNet.hostDict:
                remoteHost = self._appNet.hostDict[name]
            else:
                raise ValueError("Host name '{}' is not in the cqc network".format(name))

            addr = remoteHost.addr
            while True:
                try:
                    s = socket.socket(addr[0], addr[1], addr[2])
                    s.connect(addr[4])
                    logging.debug("App {}: Classical channel to {} opened".format(self.name, name))
                    break
                except ConnectionRefusedError:
                    logging.debug(
                        "App {}: Could not open classical channel to {}, trying again..".format(self.name, name)
                    )
                    time.sleep(self._conn_retry_time)
                except Exception as e:
                    logging.warning(
                        "App {} : Critical error when connection to app node {}: {}".format(self.name, name, e)
                    )
                    break
            self._classicalConn[name] = s

    def closeClassicalChannel(self, name):
        """
        Closes a classical connection to another host in the application network.

        - **Arguments**

            :name:        The name of the host in the application network.
        """
        if name in self._classicalConn:
            logging.debug("App {}: Closing classical channel to {}".format(self.name, name))
            s = self._classicalConn.pop(name)
            s.close()
            logging.debug("App {}: Classical channel to {} closed".format(self.name, name))

    def sendClassical(self, name, msg, close_after=True):
        """
        Sends a classical message to another host in the application network.

        - **Arguments**

            :name:        The name of the host in the application network.
            :msg:        The message to send. Should be either a int in range(0,256) or a list of such ints.
            :timout:    The time to try to connect to the server. When timout is reached an RuntimeError is raised.
        """
        if name not in self._classicalConn:
            self.openClassicalChannel(name)
        try:
            to_send = bytes([int(msg)])
        except (TypeError, ValueError):
            to_send = bytes(msg)
        logging.debug("App {}: Sending classical message {} to {}".format(self.name, to_send, name))
        self._classicalConn[name].send(to_send)
        logging.debug("App {}: Classical message {} to {} sent".format(self.name, to_send, name))
        if close_after:
            self.closeClassicalChannel(name)

    def _handle_create_qubits(self, num_qubits, notify):
        qubits = []
        for _ in range(num_qubits):
            msg = self.readMessage()
            self.check_error(msg[0])
            if msg[0].tp != CQC_TP_NEW_OK:
                raise CQCUnsuppError("Unexpected message of type {} send back from backend".format(msg[0].tp))
            qubits.append(self.parse_CQC_msg(msg))
            self.print_CQC_msg(msg)

        if notify:
            message = self.readMessage()
            self._assert_done_message(message)
            self.print_CQC_msg(message)

        return qubits

    def readMessage(self, maxsize=192):  # WHAT IS GOOD SIZE?
        """Receive the whole message from cqc server.

        Returns (CQCHeader,None,None), (CQCHeader,CQCNotifyHeader,None) 
        or (CQCHeader,CQCNotifyHeader,EntInfoHeader) depending on the 
        type of message.

        Maxsize is the max size of message.
        """

        # Initialize checks
        gotCQCHeader = False
        if self.buf:
            checkedBuf = False
        else:
            checkedBuf = True

        while True:
            # If buf does not contain enough data, read in more
            if checkedBuf:
                # Receive data
                data = self._s.recv(maxsize)

                # Read whatever we received into a buffer
                if self.buf:
                    self.buf += data
                else:
                    self.buf = data

                    # If we don't have the CQC header yet, try and read it in full.
            if not gotCQCHeader:
                if len(self.buf) < CQCHeader.HDR_LENGTH:
                    # Not enough data for CQC header, return and wait for the rest
                    checkedBuf = True
                    continue

                    # Got enough data for the CQC Header so read it in
                gotCQCHeader = True
                rawHeader = self.buf[0:CQCHeader.HDR_LENGTH]
                currHeader = CQCHeader(rawHeader)

                # Remove the header from the buffer
                self.buf = self.buf[CQCHeader.HDR_LENGTH : len(self.buf)]

                # Check for error
                self.check_error(currHeader)

                # Check whether we already received all the data
            if len(self.buf) < currHeader.length:
                # Still waiting for data
                checkedBuf = True
                continue
            else:
                break
                # We got all the data, read other headers if there is any
        if currHeader.length == 0:
            return currHeader, None, None
        else:
            if currHeader.tp == CQC_TP_INF_TIME:
                timeinfo_header = self._extract_header(CQCTimeinfoHeader)
                return currHeader, timeinfo_header, None
            elif currHeader.tp == CQC_TP_MEASOUT:
                measout_header = self._extract_header(CQCMeasOutHeader)
                return currHeader, measout_header, None
            elif currHeader.tp in [CQC_TP_RECV, CQC_TP_NEW_OK, CQC_TP_EXPIRE]:
                xtra_qubit_header = self._extract_header(CQCXtraQubitHeader)
                return currHeader, xtra_qubit_header, None
            elif currHeader.tp == CQC_TP_EPR_OK:
                xtra_qubit_header = self._extract_header(CQCXtraQubitHeader)
                ent_info_hdr = self._extract_header(EntInfoHeader)
                return currHeader, xtra_qubit_header, ent_info_hdr

    def _extract_header(self, header_class):
        """
        Extracts the given header class from the first part of the current buffer.
        :param header_class: Subclassed from `cqc.backend.cqcHeader.Header`
        :return: An instance of the class
        """
        if not issubclass(header_class, Header):
            raise ValueError("header_class {} is not a subclass of Header".format(header_class))

        try:
            rawHeader = self.buf[:header_class.HDR_LENGTH]
        except IndexError:
            raise ValueError("Got a header message of unexpected size")
        self.buf = self.buf[header_class.HDR_LENGTH: len(self.buf)]
        header = header_class(rawHeader)

        return header

    def sendQubit(self, q, name, remote_appID=0, notify=True, block=True, remote_socket=None):
        """Sends qubit to another node in the cqc network. 
        
        If this node is not in the network an error is raised.

        - **Arguments**

            :q:         The qubit to send.
            :Name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :remote_socket: tuple (str, int) of ip and port number. Needed if no cqcFile was specified
        """
        q = super().sendQubit(
            q=q,
            name=name,
            remote_appID=remote_appID,
            notify=notify,
            block=block,
            remote_socket=remote_socket,
        )

    def createEPR(self, name, remote_appID=0, notify=True, block=True, remote_socket=None):
        """Creates epr with other host in cqc network.

        - **Arguments**

            :name:         Name of the node as specified in the cqc network config file.
            :remote_appID:     The app ID of the application running on the receiving node.
            :nofify:     Do we wish to be notified when done.
            :block:         Do we want the qubit to be blocked
            :remote_socket: tuple (str, int) of ip and port number. Needed if no cqcFile was specified
        """
        return super().createEPR(
            name,
            remote_appID=remote_appID,
            notify=notify,
            block=block,
            remote_socket=remote_socket,
        )

    def _handle_epr_response(self, notify):
        # Get RECV message
        message = self.readMessage()
        otherHdr = message[1]
        entInfoHdr = message[2]
        q_id = otherHdr.qubit_id

        self.print_CQC_msg(message)

        if notify:
            message = self.readMessage()
            self.print_CQC_msg(message)

        # initialize the qubit
        q = qubit(self, createNew=False)

        q._set_entanglement_info(entInfoHdr)
        q._qID = q_id
        # Activate and return qubit
        q._set_active(True)
        return q

    def _handle_factory_response(self, num_iter, response_amount, should_notify=False):
        """Handles the responses from a factory command and returns a list of results"""
        res = []
        for _ in range(num_iter):
            for _ in range(response_amount):
                message = self.readMessage()
                self.check_error(message[0])
                # TODO handle new qubit!
                res.append(self.parse_CQC_msg(message))
                self.print_CQC_msg(message)

        if should_notify:
            message = self.readMessage()
            self.check_error(message[0])

        return res

    def return_meas_outcome(self):
        """Return measurement outcome."""

        msg = self.readMessage()

        try:
            otherHdr = msg[1]
            return otherHdr.outcome
        except AttributeError:
            raise RuntimeError("Didn't receive a measurement outcome")

        message = self.readMessage()
        self._assert_done_message(message)
        self.print_CQC_msg(message)

    def get_remote_from_directory_or_address(self, name, remote_socket=None):
        cqcNet = self._cqcNet
        if remote_socket is None:
            try:
                # Get receiving host
                hostDict = cqcNet.hostDict
            except AttributeError:
                raise ValueError(
                    "If a CQCConnections is initialized without specifying a cqcFile you need to also provide a"
                    "socket address for the remote node here."
                )
            if name in hostDict:
                recvHost = hostDict[name]
                remote_ip = recvHost.ip
                remote_port = recvHost.port
            else:
                raise ValueError("Host name '{}' is not in the cqc network".format(name))
        else:
            try:
                remote_host, remote_port = remote_socket
                if not isinstance(remote_host, str):
                    raise TypeError()
                if not isinstance(remote_port, int):
                    raise TypeError()
            except Exception:
                raise TypeError("When specifying the remote socket address, this should be a tuple (str,int).")

                # Pack the IP
            addrs = socket.getaddrinfo(remote_host, remote_port, proto=socket.IPPROTO_TCP, family=socket.AF_INET)
            addr = addrs[0]
            remote_ip = cqc_node_id_from_addrinfo(addr)
            remote_port = addr[4][1]
        return remote_ip, remote_port
