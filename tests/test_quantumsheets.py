"""
test_quantumsheets.py
---------------------
Smoke tests for the QuantumSheets rendering pipeline.  Every test builds a
circuit, renders it, and asserts the figure was created without errors.
"""
import pytest
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for CI
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit

from QuantumSheets.render import draw_circuit, StaffCircuitDrawer


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all matplotlib figures after each test to avoid memory leaks."""
    yield
    plt.close("all")


# ── Basic rendering ──────────────────────────────────────────────────

class TestDrawCircuit:
    def test_empty_circuit(self):
        qc = QuantumCircuit(2)
        fig = draw_circuit(qc)
        assert fig is not None
        assert len(fig.axes) == 1

    def test_single_qubit_gates(self):
        qc = QuantumCircuit(1)
        qc.h(0)
        qc.x(0)
        qc.z(0)
        fig = draw_circuit(qc)
        assert fig is not None

    def test_multi_qubit_gates(self):
        qc = QuantumCircuit(3)
        qc.cx(0, 1)
        qc.cz(1, 2)
        qc.swap(0, 2)
        fig = draw_circuit(qc)
        assert fig is not None

    def test_toffoli(self):
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        fig = draw_circuit(qc)
        assert fig is not None

    def test_parametric_gates(self):
        import math
        qc = QuantumCircuit(1)
        qc.rx(math.pi / 2, 0)
        qc.ry(math.pi / 4, 0)
        qc.rz(math.pi, 0)
        fig = draw_circuit(qc)
        assert fig is not None

    def test_measure(self):
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        fig = draw_circuit(qc)
        assert fig is not None

    def test_barrier(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.barrier()
        qc.x(1)
        fig = draw_circuit(qc)
        assert fig is not None


# ── Styles ───────────────────────────────────────────────────────────

class TestStyles:
    def test_ink_style(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        fig = draw_circuit(qc, style="ink")
        assert fig is not None

    def test_clean_style(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        fig = draw_circuit(qc, style="clean")
        assert fig is not None


# ── Options ──────────────────────────────────────────────────────────

class TestOptions:
    def test_strip_mode(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        fig = draw_circuit(qc, strip=True)
        assert fig is not None

    def test_title(self):
        qc = QuantumCircuit(1)
        qc.h(0)
        fig = draw_circuit(qc, title="Test Title")
        assert fig is not None

    def test_max_cols_per_system(self):
        qc = QuantumCircuit(2)
        for _ in range(10):
            qc.h(0)
            qc.cx(0, 1)
        fig = draw_circuit(qc, max_cols_per_system=4)
        assert fig is not None

    def test_save_to_file(self, tmp_path):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        out = tmp_path / "test_output.png"
        fig = draw_circuit(qc, filename=str(out), dpi=72)
        assert out.exists()
        assert out.stat().st_size > 0


# ── Comprehensive gate coverage ──────────────────────────────────────

class TestAllGateTypes:
    def test_comprehensive_circuit(self):
        """Smoke test: every gate type the library claims to support."""
        import math
        qc = QuantumCircuit(4, 2)

        # Single-qubit
        qc.h(0)
        qc.x(1)
        qc.y(2)
        qc.z(3)
        qc.s(0)
        qc.sdg(1)
        qc.t(2)
        qc.tdg(3)
        qc.sx(0)
        qc.id(1)

        # Parametric
        qc.rx(math.pi / 2, 0)
        qc.ry(math.pi / 4, 1)
        qc.rz(math.pi, 2)
        qc.p(math.pi / 3, 3)

        # Barrier
        qc.barrier()

        # Multi-qubit
        qc.cx(0, 1)
        qc.cz(2, 3)
        qc.ccx(0, 1, 2)
        qc.swap(1, 3)

        # Measurement
        qc.measure(0, 0)
        qc.measure(1, 1)

        fig = draw_circuit(qc, style="clean")
        assert fig is not None
        assert len(fig.axes) == 1
