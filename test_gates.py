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

qc.id(0)
qc.rx(math.pi/2, 1)
qc.ry(math.pi/4, 2)
qc.rz(math.pi/8, 3)
qc.p(math.pi, 4)

qc.u(math.pi/2, math.pi/4, math.pi/8, 0)
qc.barrier()

# Two qubit gates (Controls)
qc.cx(0, 1)
qc.cy(1, 2)
qc.cz(2, 3)
qc.ch(3, 4)

qc.crx(math.pi/2, 0, 2)
qc.cry(math.pi/4, 1, 3)
qc.crz(math.pi/8, 2, 4)
qc.cp(math.pi, 0, 3)
qc.cu(math.pi/2, math.pi/4, math.pi/8, 0.0, 1, 4)
qc.barrier()

# Two qubit gates (SWAP/Interactions)
qc.swap(0, 1)
qc.iswap(1, 2) if hasattr(qc, 'iswap') else None
qc.rxx(math.pi/2, 2, 3)
qc.ryy(math.pi/4, 3, 4)
qc.rzz(math.pi/8, 0, 2)
qc.rzx(math.pi, 1, 3)
qc.barrier()

# Three+ qubit gates
qc.ccx(0, 1, 2)
qc.cswap(2, 3, 4)
qc.barrier()

# Long-distance and inverted multi-qubit gates
qc.cx(3, 0)     # Control bottom, target top
qc.cy(0, 4)     # Very long distance, control top
qc.swap(1, 4)   # Long distance swap
qc.cswap(4, 0, 2) # Control bottom, targets top
qc.ccx(4, 2, 0)   # Controls bottom, target top
qc.barrier()

# Measurement and Reset
qc.reset(0)
qc.measure_all()

print("Qiskit Text Circuit:")
print(qc.draw())

try:
    qc.draw('mpl', filename='test_gates_qiskit.png')
    print("Saved Qiskit mpl drawing to test_gates_qiskit.png")
except Exception as e:
    print("Could not draw qiskit mpl:", e)
