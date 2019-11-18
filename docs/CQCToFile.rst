Writing Commands to File with CQCToFile
=======================================

If you want to write the commands to a file instead of sending them via
a server you can use :meth:`cqc.pythonLib.CQCToFile`. This class replaces
:meth:`cqc.pythonLib.CQCConnection`. 

:meth:`CQCToFile` has the following keyword arguments:

- filename: The file to which the commands will be written
- pend_messages: Whether to pend_messages until flush or to send them immediatly
- overwrite: Whether to overwrite if there is already a file with the name given as filename
