"""Render and play a quantum circuit featuring control flow loops (ForLoopOp).

Run from the repository root with: python docs/loop_circuit.py
"""

from pathlib import Path
import sys

# Allow running this example directly from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qiskit import QuantumCircuit
from QuantumSheets import draw_circuit, generate_audio

qc = QuantumCircuit(2)
qc.h(0)

# Quantum loop: body repeated 2 times
with qc.for_loop(range(2)):
    qc.cx(0, 1)
    qc.h(0)

qc.measure_all()

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    draw_circuit(qc, filename=out_dir / "loop_score.png", style="clean", strip=True, dpi=160)
    generate_audio(qc, filename=out_dir / "loop_score.wav", bpm=120)
    print("Loop circuit rendered successfully!")
