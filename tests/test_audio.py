"""Smoke tests for the audio module."""
import wave as wave_mod
import pytest
from qiskit import QuantumCircuit

from QuantumSheets.audio import generate_audio, _synthesize_piano_note


def test_generate_audio_creates_wav(tmp_path):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    out = tmp_path / "test.wav"
    generate_audio(qc, filename=str(out))
    assert out.exists()
    with wave_mod.open(str(out), 'rb') as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 44100
        assert wf.getnframes() > 0


def test_synthesize_piano_note_shape():
    note = _synthesize_piano_note(440.0, 0.5, 44100)
    assert note.shape == (22050,)
    assert note.dtype.name == "float32"


def test_synthesize_piano_note_zero_duration():
    note = _synthesize_piano_note(440.0, 0.0, 44100)
    assert len(note) == 0


def test_generate_audio_with_precomputed_moments(tmp_path):
    from QuantumSheets.layout import circuit_to_moments
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    moments = circuit_to_moments(qc)
    out = tmp_path / "test_precomputed.wav"
    generate_audio(qc, filename=str(out), moments=moments)
    assert out.exists()


def test_note_caching():
    """Second call with same params should return equal (cached) result."""
    import numpy as np
    n1 = _synthesize_piano_note(440.0, 0.5, 44100)
    n2 = _synthesize_piano_note(440.0, 0.5, 44100)
    np.testing.assert_array_equal(n1, n2)
