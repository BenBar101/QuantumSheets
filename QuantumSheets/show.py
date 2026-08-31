import qiskit
from qiskit import QuantumCircuit
import math
import os

import sys
# Allow importing QuantumSheets when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from QuantumSheets import draw_circuit

def main():
    # 1. Create a 4-qubit quantum circuit
    qc = QuantumCircuit(4)

    # State Preparation (GHZ State)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 3)
    qc.barrier()

    # Apply some rotations and a SWAP gate
    qc.rx(math.pi/2, 0)
    qc.ry(math.pi/4, 1)
    qc.rz(math.pi, 2)
    qc.s(3)
    
    # We can also chain operations
    qc.swap(0, 3)
    qc.barrier()

    # Multi-controlled gates and single qubit gates
    qc.ccx(0, 1, 2)  # Toffoli
    qc.cz(2, 3)
    qc.h(0)
    qc.h(1)
    
    # Finally, measure all qubits
    qc.measure_all()

    # 2. Render the circuit as a musical score
    output_filename = "my_circuit_score.png"
    print(f"🎨 Rendering the quantum circuit using QuantumSheets...")
    draw_circuit(qc, filename=output_filename)
    
    print(f"✨ Done! Your quantum sheet music has been saved to: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    main()
