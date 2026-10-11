"""Smoke tests for the render module."""
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for CI

import pytest
from qiskit import QuantumCircuit

from QuantumSheets import draw_circuit
from QuantumSheets.render import StaffCircuitDrawer


def test_draw_circuit_returns_figure():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    fig = draw_circuit(qc)
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_draw_circuit_saves_file(tmp_path):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    out = tmp_path / "test_output.png"
    fig = draw_circuit(qc, filename=str(out))
    assert out.exists()
    assert out.stat().st_size > 0


def test_styles():
    qc = QuantumCircuit(1)
    qc.h(0)
    for style in ("ink", "clean"):
        fig = draw_circuit(qc, style=style)
        import matplotlib.pyplot as plt
        plt.close(fig)


def test_strip_mode():
    qc = QuantumCircuit(2)
    qc.h(0)
    fig = draw_circuit(qc, strip=True)
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_multi_system():
    """Circuit wide enough to trigger multiple systems."""
    qc = QuantumCircuit(2)
    for _ in range(40):
        qc.h(0)
        qc.cx(0, 1)
    fig = draw_circuit(qc, max_cols_per_system=10)
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_empty_circuit():
    qc = QuantumCircuit(1)
    fig = draw_circuit(qc)
    import matplotlib.pyplot as plt
    plt.close(fig)
