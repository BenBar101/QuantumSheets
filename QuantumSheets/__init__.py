"""
QuantumSheets — Musical staff notation for quantum circuits.

Renders Qiskit QuantumCircuits as sheet-music-style diagrams where each
qubit is a five-line musical staff.
"""
from .layout import circuit_to_moments, GateEvent
from .render import draw_circuit, StaffCircuitDrawer
