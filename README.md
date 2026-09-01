# QuantumSheets 🎵⚛️

QuantumSheets is a Python library that bridges the worlds of quantum computing and music. It takes a Qiskit quantum circuit and visually renders it as beautiful, highly-legible sheet music. 

Instead of traditional blocky quantum circuit diagrams, QuantumSheets draws your gates as musical notes on a grand staff, with classical measurements, multi-qubit controls, and precise musical spacing. It's perfect for educational materials, presentations, and anyone who wants to see the harmony in their quantum algorithms.

## Features
- **Native Qiskit Support**: Pass in any standard `qiskit.QuantumCircuit` object.
- **Musical Aesthetics**: Notes for single-qubit gates, chords for multi-qubit gates, proper stems, and clefs!
- **MathText Rendering**: Supports full LaTeX/MathText inside gate labels (e.g., wrap your custom gate name in `$` like `"$7^{1} \\% 15$"` and it beautifully renders superscripts).
- **Multi-System Wrapping**: Automatically wraps long circuits across multiple "systems" (lines) like real sheet music.
- **Dynamic Spacing**: Gracefully expands the columns backward and forward if a gate has a very long name, perfectly mirroring professional music engraving.

## Shor's Algorithm Example

QuantumSheets can easily handle complex, multi-qubit custom logic—like this 8-qubit implementation of Shor's Algorithm (factoring $15$ with $a=7$):

![Shor's Algorithm](docs/test_shor_output.png)

This demonstrates the engine's ability to seamlessly draw multi-qubit control chords, handle long MathText labels underneath chords, and balance spacing without overcrowding the page.

## Quickstart

```python
from qiskit import QuantumCircuit
from QuantumSheets import draw_circuit

# 1. Build your Qiskit circuit
qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure_all()

# 2. Render as sheet music!
draw_circuit(qc, filename="my_circuit_score.png", strip=True)
```

## Supported Gates
Currently supported gates include:
- `X`, `Y`, `Z`, `H`, `S`, `T`
- `Rx`, `Ry`, `Rz`
- `CX` (CNOT), `CZ`, `CP`, `SWAP`
- `CCX` (Toffoli), `CSWAP`
- `Measure`, `Barrier`

## Customization
You can easily extend the aesthetic of the engine. The layout spacing, fonts, and colors are configured within the `render.py` and `assets` directories. 

## License
MIT License
