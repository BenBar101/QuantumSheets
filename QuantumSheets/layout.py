"""
layout.py
---------
Turns a qiskit QuantumCircuit into a simple, drawing-agnostic list of
"moments" (columns). Each moment holds the operations that happen at
that horizontal position, exactly the way a textbook circuit diagram
(and our staff-notation diagram) lays gates out: every wire only ever
has ONE gate per column, and a gate's column is the first free column
after all of its wires' previous gates.

This file has no matplotlib / drawing code in it on purpose, so it can
be unit-tested or reused by a different renderer later.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GateEvent:
    name: str                     # qiskit instruction name, e.g. "h", "cx", "measure"
    label: str                    # human readable label to print, e.g. "H", "CNOT", "RZ(1.57)"
    qubits: List[int]             # ALL qubit rows touched (controls + targets), in circuit order
    controls: List[int]           # subset of qubits that act as controls (empty for non-controlled gates)
    targets: List[int]            # subset of qubits that are "acted upon" (targets)
    clbits: List[int] = field(default_factory=list)
    kind: str = "generic"         # "single" | "control" | "swap" | "measure" | "barrier" | "generic"
    column: int = 0


# qiskit instruction name -> pretty label
_PRETTY = {
    "h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "sdg": "S†",
    "t": "T", "tdg": "T†", "sx": "√X", "sxdg": "√X†", "id": "I",
    "cx": "CNOT", "cy": "CY", "cz": "CZ", "ch": "CH", "swap": "SWAP",
    "ccx": "TOFFOLI", "cswap": "CSWAP", "measure": "MEAS", "barrier": "BARRIER",
    "reset": "RESET",
}

_PARAM_GATES = {"rx", "ry", "rz", "p", "u", "u1", "u2", "u3", "crx", "cry", "crz", "cp", "cu"}


def _fmt_params(params):
    out = []
    for p in params:
        try:
            out.append(f"{float(p):.2f}")
        except (TypeError, ValueError):
            out.append(str(p))
    return ",".join(out)


def _pretty_label(name, params):
    base = _PRETTY.get(name, name.upper())
    if name in _PARAM_GATES and params:
        base = f"{base}({_fmt_params(params)})"
    return base


def circuit_to_moments(qc) -> List[List[GateEvent]]:
    """
    Greedily packs qc.data into moments (columns), one gate per wire per
    column, mirroring how standard circuit diagrams (and qiskit's own
    drawer) lay things out. Returns a list of moments; each moment is a
    list of GateEvent objects sharing that column.
    """
    n_qubits = qc.num_qubits
    next_free_col = [0] * n_qubits          # next available column per qubit wire
    events: List[GateEvent] = []

    for instr in qc.data:
        op = instr.operation
        name = op.name
        if name in ("delay",):
            # timing-only instruction, irrelevant to the diagram
            continue

        q_idx = [qc.find_bit(q).index for q in instr.qubits]
        c_idx = [qc.find_bit(c).index for c in instr.clbits] if instr.clbits else []

        if not q_idx:
            continue

        col = max(next_free_col[q] for q in q_idx)

        if name == "barrier":
            kind = "barrier"
            controls, targets = [], q_idx
        elif name == "measure":
            kind = "measure"
            controls, targets = [], q_idx
        elif name == "swap":
            kind = "swap"
            controls, targets = [], q_idx
        elif len(q_idx) >= 2 and name.startswith("c") and name not in ("cswap",):
            # cx, cy, cz, ch, crx, cry, crz, cp, cu, ccx (toffoli), mcx...
            kind = "control"
            n_ctrl = len(q_idx) - 1
            controls, targets = q_idx[:n_ctrl], q_idx[n_ctrl:]
        elif name == "cswap":
            kind = "control"  # controlled-swap: draw control + swap pair as generic control group
            controls, targets = [q_idx[0]], q_idx[1:]
        elif len(q_idx) == 1:
            kind = "single"
            controls, targets = [], q_idx
        else:
            kind = "generic"
            controls, targets = [], q_idx

        label = _pretty_label(name, getattr(op, "params", []))
        ev = GateEvent(
            name=name, label=label, qubits=q_idx, controls=controls,
            targets=targets, clbits=c_idx, kind=kind, column=col,
        )
        events.append(ev)

        for q in q_idx:
            next_free_col[q] = col + 1

    if not events:
        return []

    n_cols = max(e.column for e in events) + 1
    moments: List[List[GateEvent]] = [[] for _ in range(n_cols)]
    for e in events:
        moments[e.column].append(e)
    return moments