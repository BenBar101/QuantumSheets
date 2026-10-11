"""Tests for the layout module (circuit_to_moments, parameter formatting)."""
import math
import pytest
from qiskit import QuantumCircuit

from QuantumSheets.layout import (
    circuit_to_moments,
    GateEvent,
    _fmt_one_param,
    _pretty_label,
)


# ── circuit_to_moments ────────────────────────────────────────────────

class TestCircuitToMoments:
    def test_empty_circuit(self):
        qc = QuantumCircuit(2)
        moments = circuit_to_moments(qc)
        assert moments == [] or all(len(m) == 0 for m in moments)

    def test_single_gate(self):
        qc = QuantumCircuit(1)
        qc.h(0)
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        assert len(gate_events) == 1
        assert gate_events[0].name == "h"
        assert gate_events[0].kind == "single"

    def test_bell_state(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        names = [ev.name for ev in gate_events]
        assert "h" in names
        assert "cx" in names

    def test_cx_is_control_kind(self):
        qc = QuantumCircuit(2)
        qc.cx(0, 1)
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        cx_ev = [ev for ev in gate_events if ev.name == "cx"][0]
        assert cx_ev.kind == "control"
        assert cx_ev.controls == [0]
        assert cx_ev.targets == [1]

    def test_swap_kind(self):
        qc = QuantumCircuit(2)
        qc.swap(0, 1)
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        swap_ev = [ev for ev in gate_events if ev.name == "swap"][0]
        assert swap_ev.kind == "swap"

    def test_measure_kind(self):
        qc = QuantumCircuit(2, 2)
        qc.measure([0, 1], [0, 1])
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        meas = [ev for ev in gate_events if ev.kind == "measure"]
        assert len(meas) == 2

    def test_barrier_kind(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.barrier()
        qc.h(1)
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        barriers = [ev for ev in gate_events if ev.kind == "barrier"]
        assert len(barriers) >= 1

    def test_no_trailing_empty_moments(self):
        qc = QuantumCircuit(3)
        qc.h(0)
        moments = circuit_to_moments(qc)
        # Last moment should not be empty
        if moments:
            assert len(moments[-1]) > 0 or len(moments) == 0

    def test_delay_gates_skipped(self):
        qc = QuantumCircuit(1)
        qc.delay(100, 0)
        moments = circuit_to_moments(qc)
        gate_events = [ev for m in moments for ev in m]
        assert all(ev.name != "delay" for ev in gate_events)


# ── Parameter formatting ──────────────────────────────────────────────

class TestFmtOneParam:
    def test_pi(self):
        assert _fmt_one_param(math.pi) == "π"

    def test_negative_pi(self):
        assert _fmt_one_param(-math.pi) == "-π"

    def test_pi_over_2(self):
        assert _fmt_one_param(math.pi / 2) == "π/2"

    def test_pi_over_4(self):
        assert _fmt_one_param(math.pi / 4) == "π/4"

    def test_zero(self):
        assert _fmt_one_param(0) == "0"

    def test_arbitrary_float(self):
        result = _fmt_one_param(1.23456)
        assert result == "1.23"

    def test_two_pi(self):
        assert _fmt_one_param(2 * math.pi) == "2π"


class TestPrettyLabel:
    def test_known_gate(self):
        assert _pretty_label("h", []) == "H"
        assert _pretty_label("cx", []) == "CNOT"

    def test_param_gate(self):
        label = _pretty_label("rx", [math.pi / 2])
        assert "π/2" in label
        assert label.startswith("RX(")

    def test_unknown_gate(self):
        assert _pretty_label("foo", []) == "FOO"
