import qiskit
from qiskit import QuantumCircuit
import math
import os

# Import our custom drawing library
from QuantumSheets import draw_circuit

def main():
    # 1. Create a 4-qubit quantum circuit
    qc = QuantumCircuit(3,3)
# --- First Section ---
    qc.h(0)
    qc.h(2)
    qc.cx(0, 1)

    qc.barrier()

    # --- Second Section ---
    qc.cx(2, 1)
    qc.x(2)
    qc.cx(2, 0)
    qc.x(2)

    qc.barrier()

    # --- Third Section ---
    qc.swap(0, 1)
    qc.x(0)
    qc.x(1)
    qc.cx(2, 1)
    qc.x(2)
    qc.cx(2, 0)
    qc.x(2)
    # Finally, measure all qubits (using measure instead of measure_all to avoid the implicit barrier)
    qc.measure([0, 1, 2], [0, 1, 2])

    # 2. Render the circuit as a musical score
    output_filename = "my_circuit_score.png"
    print(f"🎨 Rendering the quantum circuit using QuantumSheets...")
    draw_circuit(qc, filename=output_filename)
    
    print(f"✨ Done! Your quantum sheet music has been saved to: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    main()