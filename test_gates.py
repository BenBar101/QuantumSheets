from qiskit import QuantumCircuit
qc = QuantumCircuit(5)
qc.h(0)
qc.x(1)
qc.y(2)
qc.z(3)
qc.s(4)
qc.barrier()
qc.cx(0, 1) # target below control
qc.cx(2, 1) # target above control
qc.cx(0, 3) # long distance, target below
qc.cx(4, 2) # long distance, target above
qc.barrier()
qc.swap(0, 1)
qc.swap(1, 3)
qc.cswap(0, 2, 4)
qc.barrier()
qc.rx(1.5, 0)
qc.rz(0.5, 1)
qc.barrier()
qc.measure_all()
