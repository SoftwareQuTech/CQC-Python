CHANGELOG
=========

For more details refer to the [documentation](https://softwarequtech.github.io/SimulaQron/html/index.html).

Upcoming
--------

2020-03-04 (v3.2.1)
-------------------
- Fixed bug when releasing qubits.

2020-02-23 (v3.2.0)
-------------------
- Major refactoring of `cqc.pythonLib` which splits the code into multiple files and improved extendability by the use of abstract classes etc.

2020-01-27 (v3.1.2)
-------------------
- Allow for numpy version up to 2.0.0

2019-11-28 (v3.1.1)
-------------------
- Pending messages are now flushed when a connection is closed.

2019-10-16 (v3.1.0)
-------------------
- CQC now supports logic. That is one can send a batch of CQC-instructions to the backend which can have conditional logic based on measurement results.
  Note, that this is different from having logic in the application in the Python library since this requires communcation back and fourth from the backend to the application.
  The Python library is also updated to be able to construct these instructions.
  For examople:
  - to apply instructions a certain number of times you can now do:
    ```python
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
    ```
  - or to perform certain instructions based on a measurement outcome you can do:
    ```python
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
    ```

2019-10-16 (v3.0.4)
-------------------
- If a CQCConnection does not manage to connect to the cqc server, the used app ID is popped from the list of used ones, to be reused again.

2019-10-08 (v3.0.3)
-------------------
- Fixed bug that mixes up return messages for different application IDs

2019-05-29 (v3.0.2)
-------------------
- Updated coinflip example and added CI.
