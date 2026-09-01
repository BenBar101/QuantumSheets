"""
QuantumSheets — Musical staff notation for quantum circuits.

Renders Qiskit QuantumCircuits as sheet-music-style diagrams where each
qubit is a five-line musical staff.
"""
__version__ = "0.1.0"
__all__ = ["circuit_to_moments", "GateEvent", "draw_circuit", "StaffCircuitDrawer"]

from .layout import circuit_to_moments, GateEvent
from .render import draw_circuit, StaffCircuitDrawer
