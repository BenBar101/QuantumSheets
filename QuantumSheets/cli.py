"""
cli.py
------
Command-line interface for QuantumSheets.  Run on a .qasm or .py file
that defines a QuantumCircuit to produce a musical-staff diagram.

Usage
-----
    python -m QuantumSheets my_circuit.qasm -o output.png
    python -m QuantumSheets my_circuit.py  -o output.png --style clean
"""
import argparse
import sys
import os


def _load_circuit(path):
    """Load a QuantumCircuit from a .qasm or .py file."""
    ext = os.path.splitext(path)[1].lower()

    if ext in (".qasm",):
        from qiskit import QuantumCircuit
        return QuantumCircuit.from_qasm_file(path)

    if ext == ".py":
        # Execute the .py file; expect it to leave a 'qc' variable in its namespace.
        ns = {}
        with open(path) as f:
            exec(compile(f.read(), path, "exec"), ns)
        for name in ("qc", "circuit", "circ"):
            if name in ns:
                return ns[name]
        raise RuntimeError(
            f"Could not find a QuantumCircuit variable named 'qc', 'circuit', or 'circ' in {path}"
        )

    raise ValueError(f"Unsupported file extension: {ext!r}  (expected .qasm or .py)")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="quantumsheets",
        description="Render a quantum circuit as a musical-staff diagram.",
    )
    parser.add_argument("input", help="Path to a .qasm or .py file defining a QuantumCircuit")
    parser.add_argument("-o", "--output", default=None,
                        help="Output filename (png/svg/pdf). Default: show in window.")
    parser.add_argument("--style", choices=("ink", "clean"), default="ink",
                        help="Visual style (default: ink)")
    parser.add_argument("--dpi", type=int, default=200, help="Output resolution")
    parser.add_argument("--title", default=None, help="Optional title above the score")
    parser.add_argument("--gates-per-measure", type=int, default=3,
                        help="How many gate columns between barlines")

    args = parser.parse_args(argv)

    qc = _load_circuit(args.input)

    from .render import draw_circuit
    fig = draw_circuit(
        qc,
        filename=args.output,
        style=args.style,
        dpi=args.dpi,
        title=args.title,
        gates_per_measure=args.gates_per_measure,
    )
    if args.output:
        print(f"Saved to {args.output}")
    else:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
