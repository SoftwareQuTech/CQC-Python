Writing Commands to File with CQCToFile
=======================================

If you want to write the commands to a file instead of sending them via
a server you can use :meth:`cqc.pythonLib.CQCToFile`. This class replaces
:meth:`cqc.pythonLib.CQCConnection`. 

:meth:`CQCToFile` has the following keyword arguments:

- :code:`filename`: The file to which the commands will be written
- :code:`pend_messages`: Whether to pend_messages until :code:`flush()` or to send them immediately
- :code:`overwrite`: Whether to overwrite the file if there is already a file 
with the name given by :code:`filename`. If this is :code:`False` and there
is a file with the same name, a number will be appended to the name.

The commands will be written to the file in textform. There will also be
another file with the same name, but with 'binary' appended, which will contain
the commands in binary form (which is easier to process later).

:meth:`cqc.pythonLib.CQCToFile` does not support sending or receiving 
classical messages, sendGetTime(), allocate_qubits(), sendFactory(), create_qubits(),
tomography(), test_preparation()

-------------
Example usage
-------------

::

    from cqc.pythonLib import CQCToFile, qubit

    with CQCToFile(pend_messages=True, overwrite=True) as cqc:

        q = qubit(cqc)
        q.H()

        # More commands, except any that rely on classical communication