"""Render and play the two-qubit Qiskit Hello World (Bell-state) circuit.

Run from the repository root with: python docs/hello_world.py
"""

from pathlib import Path
import sys

# Allow running this example directly from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qiskit import QuantumCircuit
from QuantumSheets import draw_circuit
from QuantumSheets.audio import generate_audio

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent
    draw_circuit(
        qc,
        filename=output_dir / "hello_world_score.png",
        style="clean",
        strip=True,
        dpi=160,
    )
    generate_audio(qc, filename=output_dir / "hello_world_score.wav", bpm=120)
