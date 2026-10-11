"""
mapping.py
----------
Domain-level pitch mapping from quantum gate names to staff-line offsets.
Used by both the renderer and audio synthesiser so neither depends on
the other.
"""

# ── Solfège pitch mapping ─────────────────────────────────────────────
# Maps gate names to vertical offsets on the staff (in units of
# LINE_SPACING from the middle line).  Positive = higher pitch.
_SOLFEGE = {
    # Mi (bottom line)
    "reset":  -2.0,
    
    # Fa (space above bottom line)
    "rx":     -1.5,
    "ry":     -1.5,
    "rz":     -1.5,
    "crx":    -1.5,
    "cry":    -1.5,
    "crz":    -1.5,
    
    # Sol (2nd line from bottom)
    "x":      -1.0,
    "y":      -1.0,
    "z":      -1.0,
    
    # La (space below middle line)
    "t":      -0.5,
    "tdg":    -0.5,
    
    # Si (middle line)
    "id":      0.0,
    "u":       0.0,
    "cu":      0.0,
    
    # Do (space above middle line)
    "p":      +0.5,
    "cp":     +0.5,
    
    # Re (4th line from bottom)
    "h":      +1.0,
    
    # Mi (space below top line)
    "s":      +1.5,
    "sdg":    +1.5,
    
    # Fa (top line)
    "sx":     +2.0,
    "sxdg":   +2.0,
}


def _get_offset_for_name(name: str) -> float:
    """Return the staff-line offset for a gate name.
    
    Falls back to -1.5 for rotation gates (names starting with 'r')
    and 0.0 for anything else unrecognised.
    """
    if name in _SOLFEGE:
        return _SOLFEGE[name]
    if name.startswith("r"):
        return -1.5
    return 0.0
