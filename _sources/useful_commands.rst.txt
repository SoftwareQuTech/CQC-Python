Useful commands
========================

Here we list some useful methods that can be applied to a :class:`~.pythonLib.CQCConnection` object or a :class:`~.pythonLib.qubit` object below.

CQCConnection
"""""""""""""""""
The :class:`~.pythonLib.CQCConnection` is initialized with the name of the node (``string``) as an argument, an optional application ID (``int``) (if multiple Connections connect to a single node), and an optional ``pend_messages`` (``bool``) flag for when sending commands in sequence. Additionally one can specify the socket address to the corresponding CQC server. If the socket address is not explicitely specified, this is taken from the cqc config-file (default `config/cqcNodes.cfg`)

* :meth:`~.pythonLib.CQCConnection.sendQubit`: Sends the qubit q (:class:`~.pythonLib.qubit`) to the node name (``string``).
* :meth:`~.pythonLib.CQCConnection.recvQubit` Receives a qubit that has been sent to this node. 
* :meth:`~.pythonLib.CQCConnection.createEPR` Creates an EPR-pair :math:`\frac{1}{\sqrt{2}}(|00\rangle+|11\rangle)` with the node name (``string``). 
* :meth:`~.pythonLib.CQCConnection.recvEPR` Receives qubit from an EPR-pair created with another node (that called :meth:`~.pythonLib.CQCConnection.createEPR`). 
* :meth:`~.pythonLib.CQCConnection.sendClassical` Sends a classical message msg (``int`` in range(0,256) or list of such ``int`` s) to the node name (``string``). Opens a socket connection if not already opened.
* :meth:`~.pythonLib.CQCConnection.recvClassical` Receives a classical message sent by another node by :meth:`~.pythonLib.CQCConnection.sendClassical`.


qubit
"""""""""""""""""
Here are some useful commands that can be applied to a :class:`~.pythonlib.qubit` object.
A :class:`~.pythonLib. object is initialized with the corresponding :class:`~.pythonLib.CQCConnection` as input and will be in the state :math:`|0\rangle`.

* :meth:`~.pythonlib.qubit.X`, :meth:`~.pythonlib.qubit.Y`, :meth:`~.pythonlib.qubit.Z`, :meth:`~.pythonlib.qubit.H`, :meth:`~.pythonlib.qubit.K`, :meth:`~.pythonlib.qubit.T` Single-qubit gates. 
* :meth:`~.pythonlib.qubit.rot_X`, :meth:`~.pythonlib.qubit.rot_Y`, :meth:`~.pythonlib.qubit.rot_Z` Single-qubit rotations with the angle :math:`\left(\mathrm{step}\cdot\frac{2\pi}{256}\right)`. 
* :meth:`~.pythonlib.qubit.cnot`, :meth:`~.pythonlib.qubit.cphase` Two-qubit gates with q (:class:`~.pythonLib.qubit`) as target. 
* :meth:`~.pythonlib.qubit.measure` Measures the qubit and returns outcome. If inplace (``bool``) then the post-measurement state is kept afterwards, otherwise the qubit is removed (default). 


Factory and Sequences
---------------------------
When the `pend_messages` flag is set to True in the :class:`~.pythonLib.CQCConnection`, ALL commands (on both :class:`~.pythonLib.qubit` and :class:`~.pythonLib.CQCConnection`) that you create are stored in a list, to be send all at once when flushed for a :class:`~.pythonLib.CQCConnection`.

* :meth:`~.pythonLib.CQCConnection.set_pending` Set the `pend_messages` flag to True/False
* :meth:`~.pythonLib.CQCConnection.flush` Send all pending messages to the backend at once. If `do_sequence` == True then it will send `CMDSequenceHeaders` between the commands, if it is False it will add the `ACTION` flag to the commands instead.

  Return ``list``. Returns a list with measurement outcomes (``int`` 's) and :class:`~.pythonLib.qubit` depending if `MEASURE` and/or `NEW` commands were used in the sequence.
* :meth:`~.pythonLib.CQCConnection.flush_factory` Send all pending messages to the backend at once as a factory, doing the sequence num_iter (``int``) times. If `do_sequence` == True then it will send `CMDSequenceHeaders` between the commands, if it is False it will add the `ACTION` flag to the commands instead.

  Return ``list``. Returns a list with measurement outcomes (``int`` 's) and :class:`~.pythonLib.qubit` depending if `MEASURE` and/or `NEW` commands were used in the sequence.

Conditional logic
---------------------------
One can of course have conditional logic in the python library and send messages depending on this logic.
However this can become inefficient when many messages have to be sent back and fourth between the application and the backend.
For this reason, CQC also supports conditional logic natively.
For examople:

* To apply instructions a certain number of times you can now do:
  
  .. code-block:: python
  
     from cqc.pythonLib import CQCConnection, qubit, CQCMix
  
     with CQCConnection('Alice') as node:
  
        # qubit is created beforehand
        qbit = qubit(node)
     
        # Start of the CQCMix
        with CQCMix(node) as pgrm:
           qbit.X()
        
           # Start of the Factory
           # Apply H three times
           with pgrm.loop(times=3):
             qbit.H()
        
           # Y gate which is not part of
           # the loop (i.e. Factory) above
           qbit.Y()
  
* Or to perform certain instructions based on a measurement outcome you can do:
  
  .. code-block:: python
  
     from cqc.pythonLib import CQCConnection, qubit, CQCMix
  
     with CQCConnection('Alice') as node:
  
        # qubits are created beforehand
        qbit1 = qubit(node)
        qbit2 = qubit(node)
     
        # Start of the CQCMix
        with CQCMix(node) as pgrm:
     
           result = qbit1.measure()
        
           # if measurement yielded 1, apply X
           with pgrm.cqc_if(result == 1):
              qbit2.X()
        
           # else, apply H
           with pgrm.cqc_else():
              qbit2.H()


