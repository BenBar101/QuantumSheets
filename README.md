# QuantumSheets

[![PyPI](https://img.shields.io/pypi/v/QuantumSheets.svg)](https://pypi.org/project/QuantumSheets/)

QuantumSheets is a Python library that renders Qiskit quantum circuits as classical sheet music. It maps quantum gates to musical notes on a staff, providing an alternative visual representation for quantum algorithms.

## Installation

You can install QuantumSheets directly from [PyPI](https://pypi.org/project/QuantumSheets/):

```bash
pip install QuantumSheets
```

## Features

- **Universal Gate Support**: Completely supports ALL standard Qiskit gates natively, and flawlessly renders completely custom multi-qubit gates of any size.
- **Musical Notation**: Renders single-qubit gates as notes and multi-qubit gates as polyphonic chords with proper stems and clefs.
- **Audio Synthesis**: Generates `.wav` files playing the circuit's sequence. Pitches are mapped to gates, and multi-qubit gates generate beautiful harmonic intervals.
- **MathText Rendering**: Supports LaTeX/MathText in custom gate labels (e.g., `$7^{1} \\% 15$`).
- **Dynamic Layout**: Automatically wraps long circuits across multiple systems and gracefully adjusts horizontal spacing for massive labels to prevent overlap.

## Example: Shor's Algorithm

An 8-qubit implementation of Shor's Algorithm containing custom, 5-qubit mathematical control operations:

![Shor's Algorithm](docs/test_shor_output.png?v=4)

## Quickstart

```python
from qiskit import QuantumCircuit
from QuantumSheets import draw_circuit
from QuantumSheets.audio import generate_audio

qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure_all()

# Render circuit to image (supports "ink" and "clean" styles)
draw_circuit(qc, filename="circuit.png", style="clean", strip=True)

# Synthesize the circuit's audio to a WAV file
generate_audio(qc, filename="circuit.wav", bpm=120)
```

### CLI Usage

You can generate both images and audio directly from the command line:

```bash
python -m QuantumSheets.cli my_circuit.py -o output.png --style clean --audio
```

## License
MIT License
