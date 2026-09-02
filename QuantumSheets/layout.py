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
    import sympy
    from qiskit.circuit import ParameterExpression
    if isinstance(p, ParameterExpression):
        # Format ParameterExpression nicely using sympy
        expr = p.sympify()
        import numpy as np
        expr = expr.subs(float(np.pi), sympy.pi)
        expr = expr.subs(-float(np.pi), -sympy.pi)
        expr = expr.subs(float(np.pi)/2, sympy.pi/2)
        expr = expr.subs(-float(np.pi)/2, -sympy.pi/2)
        expr = sympy.nsimplify(expr, rational=True)
        return str(expr).replace('pi', 'π').replace('*', '')

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
    next_free_col = [0] * n_qubits
    events = []

    from qiskit.converters import circuit_to_dag
    from qiskit.circuit.controlflow import ForLoopOp, WhileLoopOp

    STANDARD_GATES = {'x', 'y', 'z', 'h', 's', 'sdg', 't', 'tdg', 'rx', 'ry', 'rz', 'rzz', 'cx', 'cy', 'cz', 'cp', 'swap', 'iswap', 'ccx', 'cswap', 'measure', 'barrier', 'delay', 'reset', 'p', 'u', 'u1', 'u2', 'u3', 'crx', 'cry', 'crz', 'cu'}

    def get_ordered_items(circuit, q_map, c_map):
        dag = circuit_to_dag(circuit)
        for layer in dag.layers():
            nodes = list(layer['graph'].op_nodes())
            def get_span(node):
                q_idx = [q_map[q] for q in node.qargs]
                if not q_idx: return 0
                return max(q_idx) - min(q_idx)
            nodes.sort(key=get_span)
            
            for node in nodes:
                op = node.op
                name = op.name
                
                # Check for control flow
                if isinstance(op, (ForLoopOp, WhileLoopOp)):
                    body = op.blocks[0]
                    inner_q_map = dict(zip(body.qubits, [q_map[q] for q in node.qargs]))
                    inner_c_map = dict(zip(body.clbits, [c_map[c] for c in node.cargs])) if node.cargs else {}
                    
                    q_idx = [q_map[q] for q in node.qargs]
                    yield {'type': 'marker', 'kind': 'repeat_start', 'q_idx': q_idx}
                    yield from get_ordered_items(body, inner_q_map, inner_c_map)
                    yield {'type': 'marker', 'kind': 'repeat_end', 'q_idx': q_idx}
                    continue
                    
                # Check for sub-circuits
                if name not in STANDARD_GATES and hasattr(op, 'definition') and op.definition is not None:
                    try:
                        body = op.definition
                        inner_q_map = dict(zip(body.qubits, [q_map[q] for q in node.qargs]))
                        inner_c_map = dict(zip(body.clbits, [c_map[c] for c in node.cargs])) if node.cargs else {}
                        
                        q_idx = [q_map[q] for q in node.qargs]
                        yield {'type': 'marker', 'kind': 'bracket_start', 'q_idx': q_idx, 'label': name}
                        yield from get_ordered_items(body, inner_q_map, inner_c_map)
                        yield {'type': 'marker', 'kind': 'bracket_end', 'q_idx': q_idx, 'label': name}
                        continue
                    except Exception:
                        pass
                
                q_idx = [q_map[q] for q in node.qargs]
                c_idx = [c_map[c] for c in node.cargs] if node.cargs else []
                yield {'type': 'node', 'node': node, 'q_idx': q_idx, 'c_idx': c_idx}

    initial_q_map = {q: i for i, q in enumerate(qc.qubits)}
    initial_c_map = {c: i for i, c in enumerate(qc.clbits)}
    
    items = list(get_ordered_items(qc, initial_q_map, initial_c_map))

    for item in items:
        if item['type'] == 'marker':
            q_idx = item['q_idx']
            if not q_idx: continue
            span_qubits = range(min(q_idx), max(q_idx) + 1)
            col = max((next_free_col[q] for q in span_qubits), default=0) + 1
            ev = GateEvent(
                name=item['kind'],
                kind=item['kind'],
                qubits=q_idx,
                clbits=[],
                controls=[],
                targets=q_idx,
                label=item.get('label', ''),
                params="",
                span=1,
                column=col
            )
            events.append((col, ev))
            for q in span_qubits:
                next_free_col[q] = col + 2
            continue
            
        node = item['node']
        q_idx = item['q_idx']
        c_idx = item['c_idx']
        
        op = node.op
        name = op.name
        if name in ("delay",):
            continue

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
            
        if params_str:
            ev_label = f"{ev_label}({params_str})"
            
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



        span_qubits = range(min(q_idx), max(q_idx) + 1) if is_multi else q_idx
            
        # Push the gate forward so it has empty space before it
        col = max(next_free_col[q] for q in span_qubits) + pad

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

        for q in span_qubits:
            next_free_col[q] = col + pad + 1

    # Group by column
    max_c = max(next_free_col) if events else 0
    moments = [[] for _ in range(max_c)]
    
    for c, ev in events:
        moments[c].append(ev)

    return moments