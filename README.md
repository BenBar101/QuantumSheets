# QuantumSheets 🎵⚛️

QuantumSheets is a Python library that bridges the worlds of quantum computing and music. It takes a Qiskit quantum circuit and visually renders it as beautiful, highly-legible sheet music. 

Instead of traditional blocky quantum circuit diagrams, QuantumSheets draws your gates as musical notes on a grand staff, with classical measurements, multi-qubit controls, and precise musical spacing. It's perfect for educational materials, presentations, and anyone who wants to see the harmony in their quantum algorithms.

## Features
- **Native Qiskit Support**: Pass in any standard `qiskit.QuantumCircuit` object.
- **Musical Aesthetics**: Notes for single-qubit gates, chords for multi-qubit gates, proper stems, and clefs!
- **Multi-System Wrapping**: Automatically wraps long circuits across multiple "systems" (lines) like real sheet music.
- **Strip Mode**: Toggle `strip=True` to render the entire circuit as one continuous horizontal line.
- **Smart Barriers**: Respects `measure_all()` barriers while maintaining visual cleanness.

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
