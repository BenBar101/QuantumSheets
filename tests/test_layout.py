"""
test_layout.py
--------------
Unit tests for QuantumSheets.layout — the drawing-agnostic circuit-to-moments
conversion layer.
"""
import math
import pytest
from qiskit import QuantumCircuit

from QuantumSheets.layout import (
    circuit_to_moments,
    GateEvent,
    _fmt_one_param,
    _pretty_label,
)


# ── _fmt_one_param tests ──────────────────────────────────────────────

class TestFmtOneParam:
    def test_zero(self):
        assert _fmt_one_param(0) == "0"

    def test_pi(self):
        assert _fmt_one_param(math.pi) == "π"

    def test_negative_pi(self):
        assert _fmt_one_param(-math.pi) == "-π"

    def test_pi_over_2(self):
        assert _fmt_one_param(math.pi / 2) == "π/2"

    def test_negative_pi_over_4(self):
        assert _fmt_one_param(-math.pi / 4) == "-π/4"

    def test_two_pi(self):
        assert _fmt_one_param(2 * math.pi) == "2π"

    def test_three_pi_over_4(self):
        assert _fmt_one_param(3 * math.pi / 4) == "3π/4"

    def test_non_rational_falls_back_to_decimal(self):
        result = _fmt_one_param(1.23456)
        assert result == "1.23"

    def test_string_passthrough(self):
        assert _fmt_one_param("theta") == "theta"


# ── _pretty_label tests ──────────────────────────────────────────────

class TestPrettyLabel:
    def test_known_gate(self):
        assert _pretty_label("h", []) == "H"
        assert _pretty_label("cx", []) == "CNOT"
        assert _pretty_label("ccx", []) == "TOFFOLI"

    def test_unknown_gate_uppercased(self):
        assert _pretty_label("foo", []) == "FOO"

    def test_parametric_gate(self):
        label = _pretty_label("rz", [math.pi / 2])
        assert "RZ" in label
        assert "π/2" in label

    def test_multi_param(self):
        label = _pretty_label("u", [math.pi, math.pi / 2, 0])
        assert "U" in label
        assert "π" in label
        assert "0" in label


# ── circuit_to_moments tests ─────────────────────────────────────────

class TestCircuitToMoments:
    def test_empty_circuit(self):
        qc = QuantumCircuit(2)
        moments = circuit_to_moments(qc)
        assert moments == []

    def test_single_gate(self):
        qc = QuantumCircuit(1)
        qc.h(0)
        moments = circuit_to_moments(qc)
        assert len(moments) == 1
        assert len(moments[0]) == 1
        ev = moments[0][0]
        assert ev.name == "h"
        assert ev.kind == "single"
        assert ev.column == 0

    def test_parallel_gates_share_column(self):
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.x(1)
        qc.z(2)
        moments = circuit_to_moments(qc)
        assert len(moments) == 1
        assert len(moments[0]) == 3

    def test_sequential_gates_on_same_qubit(self):
        qc = QuantumCircuit(1)
        qc.h(0)
        qc.x(0)
        qc.z(0)
        moments = circuit_to_moments(qc)
        assert len(moments) == 3
        assert moments[0][0].name == "h"
        assert moments[1][0].name == "x"
        assert moments[2][0].name == "z"

    def test_cx_detection(self):
        qc = QuantumCircuit(2)
        qc.cx(0, 1)
        moments = circuit_to_moments(qc)
        ev = moments[0][0]
        assert ev.kind == "control"
        assert ev.controls == [0]
        assert ev.targets == [1]

    def test_swap_detection(self):
        qc = QuantumCircuit(2)
        qc.swap(0, 1)
        moments = circuit_to_moments(qc)
        ev = moments[0][0]
        assert ev.kind == "swap"

    def test_measure_detection(self):
        qc = QuantumCircuit(1, 1)
        qc.measure(0, 0)
        moments = circuit_to_moments(qc)
        ev = moments[0][0]
        assert ev.kind == "measure"

    def test_barrier_detection(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.barrier()
        qc.x(0)
        moments = circuit_to_moments(qc)
        # barrier should occupy its own column
        barrier_events = [ev for m in moments for ev in m if ev.kind == "barrier"]
        assert len(barrier_events) >= 1

    def test_toffoli_control_count(self):
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        moments = circuit_to_moments(qc)
        ev = moments[0][0]
        assert ev.kind == "control"
        assert len(ev.controls) == 2
        assert len(ev.targets) == 1

    def test_delay_is_skipped(self):
        qc = QuantumCircuit(1)
        qc.delay(100, 0)
        moments = circuit_to_moments(qc)
        assert moments == []

    def test_greedy_packing(self):
        """A cx on q0,q1 followed by h on q2 should share the same column."""
        qc = QuantumCircuit(3)
        qc.cx(0, 1)
        qc.h(2)
        moments = circuit_to_moments(qc)
        assert len(moments) == 1
        assert len(moments[0]) == 2
