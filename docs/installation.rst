Installation
============

.. note::

   ``cqc`` is a library for writing applications which send CQC messages to a backend which can listen to these messages.
   This library does not come with a backend but you can use the simulator `SimulaQron <http://www.simulaqron.org/>`_ as a backend.

Install from pypi
-----------------

To install ``cqc`` from pypi do:

.. code-block:: bash
   
   pip3 install cqc

Install from source
-------------------

To install ``cqc`` from source, clone the `repo <https://github.com/SoftwareQuTech/CQC-Python>`_, cd into the folder and do:

.. code-block:: bash

   make install

To verify the installation, do:

.. code-block:: bash

   make verify
