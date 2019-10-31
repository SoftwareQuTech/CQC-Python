# Tests for the CQCToFile class

# To get a temporary directory start the function with
#
# filename=os.path.join(str(tmpdir),'CQC_File')
#
# with CQCToFile(filename=filename) as cqc:



from cqc.pythonLib import CQCToFile, qubit
import os
from cqc.cqcHeader import CQC_TP_HELLO

def test_name(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:
        assert cqc.name == 'CQCToFile'

def test_tempdir(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:

        cqc.commit('test')
         
        
        with open(filename) as f:
            contents = f.read()
            assert contents == 'test\n'

def test_sendSimple(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:
         
        cqc.sendSimple(CQC_TP_HELLO)

        with open(filename) as f:
            contents = f.read()
            print(contents)
            assert contents[6:10] == "\\x00"

def test_createqubit(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:
         
        q = qubit(cqc)

        with open(filename) as f:
            
            line = f.readline()
            print(line)

            assert line[6:10] == "\\x01"
            assert line[42:46] == "\\x01"

def test_releasequbit(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:
         
        q = qubit(cqc)

    with open(filename) as f:
            
        line = f.readline()
        line = f.readline()
        print(line)

        assert line[6:10] == "\\x01"
        assert line[42:46] == "\\x17"

def test_Hgate(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:
         
        q = qubit(cqc)
        q.H()

    with open(filename) as f:
            
        line = f.readline()
        line = f.readline()
        print(line)

        assert line[6:10] == "\\x01"
        assert line[42:46] == "\\x11"

def test_some_combinations(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:
         
        q = cqc.createEPR("Alice")
        q.H()
        a = qubit(cqc)
        a.cnot(q)
        cqc.sendQubit(a, "Alice")

        c = cqc.recvQubit()
        d = cqc.recvEPR()
        c.H()
        d.H()
        c.cnot(d)

def test_flushing(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename, pend_messages=True) as cqc:
        
        assert not cqc._pending_headers

        q = qubit(cqc)
        q.H()
        q.X()
        q.Z()

        assert cqc._pending_headers

        cqc.flush()

        assert not cqc._pending_headers 

def test_qubitIDs(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:

        a = qubit(cqc)
        a.X()
        b = qubit(cqc)
        b.Z()
        c = qubit(cqc)
        c.H()

        assert a._qID == 0
        assert b._qID == 1
        assert c._qID == 2

def test_measurement(tmpdir):

    filename=os.path.join(str(tmpdir),'CQC_File')

    with CQCToFile(filename=filename) as cqc:

        q = qubit(cqc)
        a = q.measure()
        assert a == 0