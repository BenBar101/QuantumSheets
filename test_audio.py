from qiskit import QuantumCircuit
import numpy as np

qc = QuantumCircuit(5)

# Single qubit gates
qc.x(0)
qc.h(1)
qc.s(2)
qc.t(3)
qc.y(4)
qc.barrier()

# Two qubit gates
qc.cx(0, 1)
qc.cz(1, 2)
qc.cp(np.pi/2, 2, 3)
qc.swap(3, 4)
qc.barrier()

# Three qubit gates (Toffoli / CSWAP)
qc.ccx(0, 1, 2)
qc.cswap(2, 3, 4)
qc.barrier()

# Four & Five qubit gates
qc.mcx([0,1,2], 3)
qc.mcx([0,1,2,3], 4)
qc.barrier()

