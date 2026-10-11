"""Allow running as: python -m QuantumSheets"""
import sys

def main():
    from . import __version__
    print(f"QuantumSheets v{__version__}")
    print("Usage: import QuantumSheets and use draw_circuit() or generate_audio()")
    print("See https://pypi.org/project/QuantumSheets/ for documentation.")

if __name__ == '__main__':
    main()
