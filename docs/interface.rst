CQC Interface 
=============

^^^^^^^^^^^^^
Introduction
^^^^^^^^^^^^^

Here we specifiy the CQC message interface. For programming SimulaQron via the CQC Interface using the Python or C provided, you do not need to know the extend of this message format. The below will be necessary, if you want to write your own library in another language. The easiest way of programming SimulaQron is via the Python CQC lib, so we recommend to get started there. Documentation of how to use the Python CQC lib can be found here :doc:`usage`: and examples here
:doc:`examples`.

Upon establishing a connection to the CQC Backend, the following packet format can be used to issue commands to the simulated quantum network. Each interaction to and from the interface starts with a CQC Header, followed by additional headers as appropriate to the message type. 

When accessing the interface directly, you must keep track of qubit IDs for each application ID yourself. It is a deliberate choice that the CQC Backend does not itself keep track of qubit or application IDs, leaving such management to you (and indeed higher levels of abstraction if you wish).
When a qubit is created with the command `CQC_CMD_NEW` a CQC message will be returned of the type `CQC_TP_NEW_OK` followed by a CQCXtraQubitHeader containing the qubit ID.
Note that if the option notify, see below, is set to true a message of type `CQC_TP_DONE` will also be returned, after the notification header, saying that the command is finished.

^^^^^^^^^^^^^^^^^^^^^
Header definitions
^^^^^^^^^^^^^^^^^^^^^

""""""""""
CQC Header
""""""""""
The `CQC header` indicates the start of a new CQC program. Therefore, every CQC program must start with a `CQC header`. The end of the program is indicated by the `length` field of this header, which contains the number of bytes following this header which constitute the current CQC program. NOTE: CQC defines many headers, but *the* `CQC header` is one specific header.

=========== ============================  =========  ===================================================================
Function    Type                          Length     Comment
=========== ============================  =========  ===================================================================
version     unsigned integer (uint8_t)    1 byte      Current version is 2
type        unsigned integer (uint8_t)    1 byte      Message type (see below)
app_id      unsigned integer (uint16_t)   2 bytes     Application ID, return messages will be tagged appropriately 
length      unsigned integer (uint32_t)   4 bytes     Total length of the CQC instruction packet (excluding this header)
=========== ============================  =========  ===================================================================


Possible message types are listed below. Depending on the message type additional headers may be required as specified below::

	class CQCType(IntEnum):
		HELLO		= 	0  # Alive check
		COMMAND		= 	1  # Execute a command list
		FACTORY		=	2  # Start executing command list repeatedly
		EXPIRE		=	3  # Qubit has expired
		DONE 		=	4  # Done with command
		RECV 		=	5  # Received qubit
		EPR_OK 		=	6  # Created EPR pair
		MEASOUT		=	7  # Measurement outcome
		GET_TIME	=	8  # Get creation time of qubit
		INF_TIME	=	9  # Return timinig information
		NEW_OK		=	10  # Created a new qubit
		MIX		=	11  # Indicate that the CQC program will contain multiple header types
		IF		=	12  # Announce a CQC IF header

		ERR_GENERAL	=	20  # General purpose error (no details
		ERR_NOQUBIT	=	21  # No more qubits available
		ERR_UNSUPP	=	22  # No sequence not supported
		ERR_TIMEOUT	=	23  # Timeout
		ERR_INUSE	=	24  # Qubit already in use
		ERR_UNKNOWN	=	25  # Unknown qubit ID

""""""""""""""""""
CQC Command Header
""""""""""""""""""

If the message type is :code:`CQC_TP_COMMAND`, :code:`CQC_TP_FACTORY` or :code:`CQC_TP_GET_TIME`, then the following additional command header must be supplied. It identifies the specific instruction to execute, as well as the qubit ID on which to perform this instructions. For rotations, two qubit gates, request to send or receive, and produce entanglement, the additional headers are required supplying further information.

If :code:`CQC_OPT_NOTIFY` set to true, each of these commmands return a CQC message of type :code:`CQC_TP_DONE`. Some commands also return additional messages before the optional done-message, as described below:

* :code:`CQC_CMD_NEW`: Returns :code:`CQC_TP_NEW_OK` followed by a :code:`CQCXtraQubitHeader` containing the qubit ID.
* :code:`CQC_CMD_MEASURE(_INPLACE)`: Returns :code:`CQC_TP_MEASOUT` followed by a :code:`CQCMeasOutHeader` containing the measurement outcome.
* :code:`CQC_CMD_RECV`: Returns :code:`CQC_TP_RECV` followed by a :code:`CQCXtraQubitHeader` containing the qubit ID.
* :code:`CQC_CMD_EPR(_RECV)`: Returns :code:`CQC_TP_EPR_OK` followed by :code:`CQCXtraQubitHeader` and an entanglement information header.

Example sequences of headers:

* `CQCHeader` (type :code:`CQC_TP_COMMAND`)
* `CQCCmdHeader` (instr :code:`CQC_CMD_ROT_X`)
* `CQCRotationHeader` (specifying the angle)
* `CQCCmdHeader` (instr :code:`CQC_CMD_Z`)


An example with factory that does X rotation, then a Z gate, 4 times:

* `CQCHeader` (type :code:`CQC_TP_FACTORY`)
* `CQCFactoryHeader` (:code:`num_iter = 4`)
* `CQCCmdHeader` (instr :code:`CQC_CMD_ROT_X`)
* `CQCRotationHeader` (specifying the angle)
* `CQCCmdHeader` (instr :code:`CQC_CMD_Z`)





=========== ============================  ==========  ===============================================================
Function    Type                          Length      Comment
=========== ============================  ==========  ===============================================================
qubit_id     unsigned int (uint16_t)       2 bytes     Qubit ID to perform the operation on
instr	     unsigned int (uint8_t)        1 byte      Instruction to perform (see below)
options	     unsigned int (uint8_t)        1 byte      Options when executing the command
=========== ============================  ==========  ===============================================================

The value of instr can be any of the following::

	/* Possible commands */
	#define CQC_CMD_I		0	/* Identity (do nothing, wait one step) */
	#define CQC_CMD_NEW		1	/* Ask for a new qubit */
	#define CQC_CMD_MEASURE		2	/* Measure qubit */
	#define CQC_CMD_MEASURE_INPLACE	3	/* Measure qubit inplace */
	#define CQC_CMD_RESET		4	/* Reset qubit to |0> */
	#define CQC_CMD_SEND		5	/* Send qubit to another node */
	#define CQC_CMD_RECV		6	/* Ask to receive qubit */
	#define CQC_CMD_EPR		7	/* Create EPR pair with the specified node */
	#define CQC_CMD_EPR_RECV	8	/* Create EPR pair with the specified node */

	#define CQC_CMD_X		10	/* Pauli X */
	#define CQC_CMD_Z		11	/* Pauli Z */
	#define CQC_CMD_Y		12	/* Pauli Y */
	#define CQC_CMD_T		13	/* T Gate */
	#define CQC_CMD_ROT_X		14	/* Rotation over angle around X in pi/256 increments */
	#define CQC_CMD_ROT_Y		15	/* Rotation over angle around Y in pi/256 increments */
	#define CQC_CMD_ROT_Z		16	/* Rotation over angle around Z in pi/256 increments */
	#define CQC_CMD_H		17	/* Hadamard Gate */
	#define CQC_CMD_K		18	/* K Gate - taking computational to Y eigenbasis */

	#define CQC_CMD_CNOT		20	/* CNOT Gate with this as control */
	#define CQC_CMD_CPHASE		21	/* CPHASE Gate with this as control */

	#define CQC_CMD_ALLOCATE	22	/* Allocate a number of qubits */
	#define CQC_CMD_RELEASE		23	/* Release a qubit */

	/* Command options */
	#define CQC_OPT_NOTIFY		0x01	/* Send a notification when cmd done */
	#define CQC_OPT_ACTION		0x02	/* Deprecated. The value of this option has no effect. */
	#define CQC_OPT_BLOCK 		0x04	/* Block until command is done */
	#define CQC_OPT_IFTHEN		0x08	/* Execute command after done */

"""""""""""""""
CQC Xtra Header
"""""""""""""""

**The CQCXtraHeader is deprecated and will be removed in the future. It is split up in multiple headers now.**
Additional header containing further information. 
The following commands require an xtra header when issued to the CQC Backend: CQC_CMD_SEND, CQC_CMD_RECV, CQC_CMD_CPHASE, CQC_CMD_CNOT, CQC_CMD_ROT_X, CQC_CMD_ROT_Y, CQC_CMD_ROT_Z

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
xtra_qubit_id  unsigned int (uint16_t)       2 bytes     ID of the target qubit in a 2 qubit controlled gate
remote_app_id  unsigned int (uint16_t)       2 bytes     Remote Application ID
remote_node    unsigned int (uint32_t)       4 bytes     IP of the remote node (IPv4)
cmdLength      unsigned int (uint32_t)       4 bytes     Length of the additional commands to execute upon completion.
remote_port    unsigned int (uint16_t)       2 bytes     Port of the remode node for sending classical control info
steps          unsigned int (uint8_t)        1 byte      Angle step of rotation (ROT) OR number of repetitions (FACTORY)
unused         unsigned int (uint8_t)        1 byte      4 byte align
============== ============================  ==========  ===============================================================

"""""""""""""""""""
CQC Assign Header
"""""""""""""""""""
Additional header used to store a measurement outcome in the backend and assign it a reference ID. Every measurement command (`CQC_CMD_MEASURE` or `CQC_CMD_MEASURE_INPLACE`) is followed by a `CQC Assign Header`. The value can be retrieved by future instructions by refering to this ID. Currently, only the `CQC If Header`_ supports retrieving measurement outcomes by reference ID.

============== ============================  ==========  ===============================================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================================
reference ID   unsigned int (uint32_t)        4 bytes    Reference ID to which to assign the value that the preceding header yielded
============== ============================  ==========  ===============================================================================

"""""""""""""""""""
CQC Rotation Header
"""""""""""""""""""
Additional header used to define the rotation angle of a rotation gate.

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
step            unsigned int (uint8_t)        1 bytes    Angle step of rotation (increments in 1/256 per step)
============== ============================  ==========  ===============================================================

""""""""""""""""""""""
CQC Extra Qubit Header
""""""""""""""""""""""
Additional header used to send a qubit_id

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
qubit_id       unsigned int (uint16_t)       2 bytes     Qubit_id of the target qubit
============== ============================  ==========  ===============================================================

""""""""""""""""""""""""
CQC Communication Header
""""""""""""""""""""""""
Additional header used to send to which node to send information to. Used in send and EPR commands.

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
remote_app_id  unsigned int (uint16_t)       2 bytes     Remote Application ID
remote_port    unsigned int (uint16_t)       2 bytes     Port of the remode node for sending classical control info
remote_node    unsigned int (uint32_t)       4 bytes     IP of the remote node (IPv4)
============== ============================  ==========  ===============================================================

""""""""""""""""""""""""
CQC Factory Header
""""""""""""""""""""""""
Additional header used to send factory information. Factory commands are used to tell the backend to do the following command or a sequence of commands multiple times.

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
num_iter       unsigned int (uint8_t)        1 byte      Number of iterations to do the sequence
options	       unsigned int (uint8_t)        1 byte      Options when executing the factory
============== ============================  ==========  ===============================================================

The value of options can be any of the following::

#define CQC_OPT_NOTIFY		0x01	/* Send a notification when cmd is done */
#define CQC_OPT_BLOCK 		0x04	/* Block until factory is done */

"""""""""""""""""
CQC Notify Header
"""""""""""""""""

**The CQCNotifyHeader is deprecated and will be removed in the future. It is split up in `CQCXtraQubitHeader`, `CQCMeasOutHeader`and `CQCTimeinfoHeader` now.**
In some cases, the CQC Backend will return notifications to the client that require additional information. For example, where a qubit was received from, the lifetime of a qubit, the measurement outcome etc.

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
qubit_id       unsigned int (uint16_t)       2 bytes     ID of the received qubit
remote_app_id  unsigned int (uint16_t)       2 bytes     Remote application ID
remote_node    unsigned int (uint32_t)       4 bytes     IP of the remote node
datetime       unsigned int (uint64_t)       8 bytes     Time of creation
remote_port    unsigned int (uint16_t)       2 bytes     Port of the remote node for sending classical control info
outcome        unsigned int (uint8_t)        1 byte      Measurement outcome
unused         unsigned int (uint8_t)        1 byte      4 byte align
============== ============================  ==========  ===============================================================

""""""""""""""""""""""
CQC Meas Out Header
""""""""""""""""""""""
Additional header used to send the outcome of a measurement.

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
meas_out       unsigned int (uint8_t)        1 byte      Measurement outcome
============== ============================  ==========  ===============================================================

""""""""""""""""""""""
CQC Timeinfo Header
""""""""""""""""""""""
Additional header used to send time information (return of `CQC_TP_GET_TIME`).

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
datetime       unsigned int (uint64_t)       8 bytes     Time of creation
============== ============================  ==========  ===============================================================

"""""""""""""""""""""""""""""""
Entanglement Information Header
"""""""""""""""""""""""""""""""

When an EPR-pair is created the CQC Backend will return information about the entanglement which can be used in a entanglement management protocol.
The entanglement information header contains information about the parties that share the EPR-pair, the time of creation, how good the entanglement is (goodness).
Furthermore, the entanglement information header contain a entanglement ID (id_AB) which can be used to keep track of the entanglement in the network.
The entanglement ID is incremented with respect to the pair of nodes and who initialized the entanglement (DF).
For this reason the entanglement ID together with the nodes and the directionality flag gives a unique way to identify the entanglement in the network.

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
node_A         unsigned int (uint32_t)       4 bytes     IP of this node
port_A         unsigned int (uint16_t)       2 bytes     Port of this node
app_id_A       unsigned int (uint16_t)       2 bytes     App ID of this node
node_B         unsigned int (uint32_t)       4 bytes     IP of other node
port_B         unsigned int (uint16_t)       2 bytes     Port of other node
app_id_B       unsigned int (uint16_t)       2 byte      App ID of other node
id_AB          unsigned int (uint32_t)       4 byte      Entanglement ID
timestamp      unsigned int (uint64_t)       8 byte      Time of creation
ToG            unsigned int (uint64_t)       8 byte      Time of goodness
goodness       unsigned int (uint16_t)       2 byte      Goodness (estimate of the fidelity of state)
DF             unsigned int (uint8_t)        1 byte      Directionality flag (0=Mid-source, 1=node_A, 2=node_B)
unused         unsigned int (uint8_t)        1 byte      4 byte align
============== ============================  ==========  ===============================================================


"""""""""""""""""""""""""""""""
CQC Type Header
"""""""""""""""""""""""""""""""
In CQC, all headers are *announced* by a preovious header of a higher level (except the CQC header, which is is announced by the absence of a previous header). The parser depends on these announcements to know how to interpret an incoming stream of bytes. Simple CQC programs contqain only one type of header, which is indicated by the `type` field of the CQC header. The `CQC type header` makes it possible to construct CQC programs which are built up of multiple types. The `CQC type header` must be used if and only if the `type` field of the CQC header is set to type `MIX` (i.e. 11). In a CQC program of type `MIX`, every block of headers which would otherwise require its own CQC header, is preceded by a `CQC type header`, which indicates the type of the following block of headers. 

============== ============================  ==========  ===============================================================
Function       Type                          Length      Comments
============== ============================  ==========  ===============================================================
type           unsigned int (uint8_t)        1 bytes     Type of next header. Any of the types `CQC Header`_ supports, except type `Mix`.
length         unsigned int (uint32_t)       4 bytes     Number of bytes until the next `type header`
============== ============================  ==========  ===============================================================


"""""""""""""""""""""""""""""""
CQC If Header
"""""""""""""""""""""""""""""""
The If header can only be used inside programs of type `Mix`. It enables comparison of a measurement outcome to a value in the backend. 

========================= ============================ ========== ===============================================================
Function				  Type                         Length     Comments
========================= ============================ ========== ===============================================================
first operand        	  unsigned int (uint32_t)      4 bytes    Reference ID of the first operand
operator                  unsigned int (uint8_t)       1 byte     Operator ID. See table below.
type of second operand    unsigned int (uint8_t)       1 byte     Can be 0 or 1. 0 means value, 1 means reference ID
second operand         	  unsigned int (uint32_t)      4 bytes    Reference ID or value of the second operand
length                    unsigned int (uint32_t)      4 bytes    Number of bytes to skip if the conditional is *False*.
========================= ============================ ========== ===============================================================

Field `operator` can be any of the following comparison operators::

	Equality	0
	Inequality	1

The field `type of second operand` indicates whether `second operand` is a value or a reference ID. This enables comparison of a reference to a value, as well as comparison of a reference to another reference.