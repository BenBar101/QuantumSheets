"""Render and play a 4-qubit circuit featuring multi-controlled gates,
parameter expressions, SWAP, and classical register measurements.

Run from the repository root with: python docs/my_circuit.py
"""

from pathlib import Path
import sys
import math

# Allow running this example directly from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qiskit import QuantumCircuit
from QuantumSheets import draw_circuit, generate_audio

qc = QuantumCircuit(4)

# 1. State preparation (GHZ state)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.cx(2, 3)
qc.barrier()

# 2. Rotations and SWAP
qc.rx(math.pi / 2, 0)
qc.ry(math.pi / 4, 1)
qc.rz(math.pi, 2)
qc.s(3)
qc.swap(0, 3)
qc.barrier()

# 3. Multi-controlled gates and single-qubit gates
qc.ccx(0, 1, 2)
qc.cz(2, 3)
qc.h(0)
qc.h(1)

# 4. Measure all qubits
qc.measure_all()

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    draw_circuit(qc, filename=out_dir / "my_circuit_score.png", style="clean", strip=True, dpi=200)
    generate_audio(qc, filename=out_dir / "my_circuit_score.wav", bpm=120)
    print("my_circuit rendered successfully!")
