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
import math
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
    params: str = ""              # Formatted parameter string
    span: int = 1                 # Number of columns this gate occupies horizontally
    column: int = 0


# qiskit instruction name -> pretty label
_PRETTY = {
    "h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "sdg": r"S$^{\,\dagger}$",
    "t": "T", "tdg": r"T$^{\,\dagger}$", "sx": "√X", "sxdg": r"√X$^{\,\dagger}$", "id": "I",
    "cx": "CNOT", "cy": "CY", "cz": "CZ", "ch": "CH", "swap": "SWAP",
    "ccx": "TOFFOLI", "cswap": "CSWAP", "measure": "MEAS", "barrier": "BARRIER",
    "reset": "RESET",
}

_PARAM_GATES = {"rx", "ry", "rz", "p", "u", "u1", "u2", "u3", "crx", "cry", "crz", "cp", "cu"}

def _fmt_one_param(p):
    """Format a single parameter, using π notation when possible."""
    try:
        val = float(p)
    except (TypeError, ValueError):
        return str(p)

    if val == 0:
        return "0"

    # Try to express as a rational multiple of π: val ≈ (n/d)·π
    ratio = val / math.pi
    # Check simple fractions: n/d for d in 1..12
    for denom in range(1, 13):
        numer = round(ratio * denom)
        if abs(numer / denom - ratio) < 1e-6 and numer != 0:
            if denom == 1:
                if numer == 1:
                    return "π"
                if numer == -1:
                    return "-π"
                return f"{numer}π"
            else:
                sign = "-" if numer < 0 else ""
                numer = abs(numer)
                if numer == 1:
                    return f"{sign}π/{denom}"
                return f"{sign}{numer}π/{denom}"

    # Fallback to decimal
    return f"{val:.2f}"


def _fmt_params(params):
    return ",".join(_fmt_one_param(p) for p in params)


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
    multi_col_spans = {}

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

        is_multi = len(q_idx) > 1 and name != "barrier"

        if name == "barrier":
            kind = "barrier"
            controls, targets = [], q_idx

        elif name == "measure":
            kind = "measure"
            controls, targets = [], q_idx
        elif name == "swap":
            kind = "swap"
            controls, targets = [], q_idx
        elif hasattr(op, "num_ctrl_qubits") and op.num_ctrl_qubits > 0:
            kind = "control"
            n_ctrl = op.num_ctrl_qubits
            controls, targets = q_idx[:n_ctrl], q_idx[n_ctrl:]
        elif len(q_idx) == 1:
            kind = "single"
            controls, targets = [], q_idx
        else:
            kind = "generic"
            controls, targets = [], q_idx

        if hasattr(op, "label") and op.label:
            ev_label = str(op.label)
        elif name in _PRETTY:
            ev_label = _PRETTY[name]
        elif kind == "single":
            if name.startswith("r") and len(name) == 2:
                ev_label = name.upper()
            else:
                ev_label = name.capitalize()
        else:
            ev_label = name.upper()

        params_str = ""
        if hasattr(op, "params") and op.params and kind not in ("measure", "barrier"):
            params_str = _fmt_params(op.params)
            
        # Determine gate padding (how many extra columns it needs on each side)
        import re
        visual_label = re.sub(r'\\[a-zA-Z]+', '', ev_label) # remove \ commands like \dagger, \pi, \pm
        visual_label = re.sub(r'[\$\{\}\\\^]', '', visual_label) # remove $, {, }, \, ^
        
        total_len = max(len(visual_label), len(params_str))
        
        # A column (DX=1.6) fits about 4-5 characters. 
        # pad=1 adds a column on BOTH sides (total 3 columns, ~14 chars)
        pad = 0
        if total_len > 3:
            pad = (total_len - 1) // 5
            
        # Push the gate forward so it has empty space before it
        col = max(next_free_col[q] for q in q_idx) + pad
            
        if is_multi:
            min_q, max_q = min(q_idx), max(q_idx)
            # Find a column where this gate (including padding) doesn't vertically overlap
            while True:
                overlap = False
                for c_offset in range(-pad, pad + 1):
                    spans = multi_col_spans.get(col + c_offset, [])
                    for (sq_min, sq_max) in spans:
                        if not (max_q < sq_min or min_q > sq_max):
                            overlap = True
                            break
                    if overlap:
                        break
                if overlap:
                    col += 1
                else:
                    for c_offset in range(-pad, pad + 1):
                        multi_col_spans.setdefault(col + c_offset, []).append((min_q, max_q))
                    break

        ev = GateEvent(
            name=name,
            kind=kind,
            qubits=q_idx,
            clbits=c_idx,
            controls=controls,
            targets=targets,
            label=ev_label,
            params=params_str,
            span=pad * 2 + 1,
            column=col
        )
        events.append((col, ev))

        for q in q_idx:
            next_free_col[q] = col + pad + 1

    # Group by column
    max_c = max(next_free_col) if events else 0
    moments = [[] for _ in range(max_c)]
    
    for c, ev in events:
        moments[c].append(ev)

    return moments