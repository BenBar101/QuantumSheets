from qiskit import QuantumCircuit
import math

qc = QuantumCircuit(5)

# Single qubit gates
qc.h(0)
qc.x(1)
qc.y(2)
qc.z(3)
qc.s(4)

qc.sdg(0)
qc.t(1)
qc.tdg(2)
qc.sx(3)
qc.sxdg(4)
qc.barrier()

qc.cx(0, 1)
qc.cy(1, 2)
qc.cz(2, 3)
qc.ch(3, 4)
qc.barrier()

qc.measure_all()

try:
    qc.draw('mpl', filename='test_short_qiskit.png')
except:
    pass
