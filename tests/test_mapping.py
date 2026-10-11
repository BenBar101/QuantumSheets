"""Tests for the mapping module (solfège pitch offsets)."""
from QuantumSheets.mapping import _SOLFEGE, _get_offset_for_name


def test_known_gates_have_offsets():
    assert _get_offset_for_name("h") == 1.0
    assert _get_offset_for_name("x") == -1.0
    assert _get_offset_for_name("id") == 0.0
    assert _get_offset_for_name("reset") == -2.0


def test_rotation_gate_default():
    # Unknown rotation gates should fall back to -1.5
    assert _get_offset_for_name("rfoo") == -1.5


def test_unknown_gate_default():
    assert _get_offset_for_name("totally_unknown") == 0.0


def test_solfege_dict_is_complete():
    # Smoke test: all values should be floats in [-2, 2]
    for name, offset in _SOLFEGE.items():
        assert isinstance(offset, float)
        assert -2.0 <= offset <= 2.0, f"{name} has offset {offset} outside [-2, 2]"
