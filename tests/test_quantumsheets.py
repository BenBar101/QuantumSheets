#!/usr/bin/env python3
"""
test_quantumsheets.py
--------------------
Comprehensive test: builds a circuit with every gate type the QuantumSheets
package is designed to handle, renders it, and saves a PNG.
"""
import sys, os

# Allow importing QuantumSheets as a package from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qiskit import QuantumCircuit
from QuantumSheets.render import draw_circuit

# ---------- build a circuit with every gate type ----------
qc = QuantumCircuit(4, 2)

# Single-qubit gates
qc.h(0)
qc.x(1)
qc.z(2)

# Parametric gate
qc.rz(1.5708, 3)   # ≈ π/2

# Barrier
qc.barrier()

# CNOT (cx)  —  control on q0, target on q1
qc.cx(0, 1)

# CZ  —  control on q2, target on q3
qc.cz(2, 3)

# Toffoli  —  controls on q0,q1, target on q2
qc.ccx(0, 1, 2)

# SWAP  —  swap q1 and q3
qc.swap(1, 3)

# Another barrier
qc.barrier()

# More single-qubit for variety
qc.h(2)
qc.x(0)

# Measurements
qc.measure(0, 0)
qc.measure(1, 1)

print(f"Circuit: {qc.num_qubits} qubits, {qc.num_clbits} classical bits")
print(f"Operations: {len(qc.data)}")
print()
print(qc.draw(output="text"))
print()

# ---------- render ----------
out_dir = os.path.dirname(os.path.abspath(__file__))
fname = os.path.join(out_dir, "test_clean.png")

fig = draw_circuit(
    qc,
    filename=fname,
    style="clean",
    title="Quantum Circuit — Staff Notation",
    dpi=200,
    gates_per_measure=3,
)
import matplotlib.pyplot as plt
plt.close(fig)
print(f"✓  Saved {fname}")
print("\nDone.")
