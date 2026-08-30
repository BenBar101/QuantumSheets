# QuantumSheets

Renders Qiskit QuantumCircuits as sheet-music-style diagrams where each qubit is a five-line musical staff.

## Installation

You can install the package directly from this repository:

```bash
pip install .
```

## Usage

```bash
python -m QuantumSheets my_circuit.qasm -o output.png
python -m QuantumSheets my_circuit.py -o output.png --style clean
```

Or using the CLI directly:

```bash
quantumsheets my_circuit.py -o output.png
```
