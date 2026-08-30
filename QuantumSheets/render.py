"""
render.py
---------
Draws a qiskit QuantumCircuit as a "musical staff" diagram: one 5-line
staff per qubit, a real treble-clef glyph, filled/hollow noteheads with
stems for gates, an X-notehead for measurements, a proper circle-plus
target for CNOT, crossing lines for SWAP, and a text label under (or
beside) every symbol naming exactly which gate it is -- so it looks like
sheet music but reads like a circuit diagram.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch
from matplotlib.path import Path
import matplotlib.patches as mpatches

from .layout import circuit_to_moments, GateEvent
from .brace import draw_vertical_brace

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONT_PATH = os.path.join(_HERE, "Euterpe.ttf")

# Candidate music-symbol fonts in preference order
_FALLBACK_FONTS = [
    "/System/Library/Fonts/Apple Symbols.ttf",   # macOS
    "/usr/share/fonts/truetype/noto/NotoMusic-Regular.ttf",  # Linux (Noto)
]

# Musical Symbols block -- see glyph catalogue.
GLYPH = {
    "gclef": "\U0001D11E",
    "barline": "\U0001D100",
    "final_barline": "\U0001D102",
    "notehead_black": "\U0001D158",
    "notehead_white": "\U0001D157",
    "x_notehead": "\U0001D143",
}

STYLES = {
    "ink": dict(bg="#efe4c9", ink="#1f4d36", accent="#c99a2e", paper_edge="#d8c79f"),
    "clean": dict(bg="#ffffff", ink="#1a1a1a", accent="#b8860b", paper_edge="#ffffff"),
}

# ── Geometry ──────────────────────────────────────────────────────────
# All units are "staff units": 1 unit = distance between two staff lines
LINE_SPACING = 0.55          # ← tighter lines, like real sheet music
N_LINES = 5
STAFF_HEIGHT = (N_LINES - 1) * LINE_SPACING
STAFF_GAP = 1.8              # ← closer staves (was 3.4)
DX = 2.0                     # horizontal step per moment column
MEASURE_GAP = 0.8
X_START = 4.0
LEFT_LABEL_X = 1.5
CLEF_X = 2.35
BRACE_X = 0.45

# Note stem length (in staff units)
STEM_LEN = 2.0

# deterministic small pitch variety for single-qubit gates (purely decorative;
# which STAFF a note sits on -- not its height -- is what carries meaning)
_PITCH_OFFSET = {
    "h": 0.3, "x": -0.3, "y": 0.6, "z": -0.6, "s": 0.6, "sdg": -0.6,
    "t": 0.0, "tdg": 0.0, "sx": 0.3, "sxdg": -0.3, "id": 0.0, "reset": -0.6,
}

_MUSIC_FONT_PROP = None  # cached after first call


def _music_font():
    """Return a FontProperties that can render music-symbol glyphs, or None."""
    global _MUSIC_FONT_PROP
    if _MUSIC_FONT_PROP is not None:
        return _MUSIC_FONT_PROP if _MUSIC_FONT_PROP != "NONE" else None

    candidates = [_FONT_PATH] + _FALLBACK_FONTS
    for path in candidates:
        if os.path.isfile(path):
            try:
                fm.fontManager.addfont(path)
                _MUSIC_FONT_PROP = fm.FontProperties(fname=path)
                return _MUSIC_FONT_PROP
            except Exception:
                continue
    # No music font found — callers will draw a text fallback.
    _MUSIC_FONT_PROP = "NONE"
    return None


def _pitch_offset(ev: GateEvent) -> float:
    if ev.name in _PITCH_OFFSET:
        return _PITCH_OFFSET[ev.name]
    return 0.4 if (hash(ev.name) % 2 == 0) else -0.4


class StaffCircuitDrawer:
    def __init__(self, qc, style="clean", gates_per_measure=3, title=None):
        self.qc = qc
        self.n_qubits = qc.num_qubits
        self.style = STYLES[style]
        self.gates_per_measure = max(1, gates_per_measure)
        self.title = title
        self.music_prop = _music_font()
        self.moments = circuit_to_moments(qc)
        self.n_cols = len(self.moments)

        self.xs = self._compute_column_xs()
        self.end_x = (self.xs[-1] if self.xs else X_START) + DX * 0.6 + 0.6

    # ---------- geometry helpers ----------
    def _compute_column_xs(self):
        xs = []
        x = X_START
        for c in range(self.n_cols):
            if c > 0 and c % self.gates_per_measure == 0:
                x += MEASURE_GAP
            xs.append(x)
            x += DX
        return xs

    def _staff_top_y(self, qubit: int) -> float:
        # qubit 0 = top staff
        return -qubit * (STAFF_HEIGHT + STAFF_GAP)

    def _mid_y(self, qubit: int) -> float:
        return self._staff_top_y(qubit) - (N_LINES // 2) * LINE_SPACING

    def _y_of(self, qubit: int, offset: float = 0.0) -> float:
        return self._mid_y(qubit) + offset * LINE_SPACING

    def _measure_barline_xs(self):
        bl = []
        for c in range(self.gates_per_measure, self.n_cols, self.gates_per_measure):
            bl.append((self.xs[c - 1] + self.xs[c]) / 2.0)
        return bl

    # ---------- drawing primitives ----------
    def _text(self, ax, x, y, s, size=10.5, weight="normal", style="normal",
              color=None, ha="center", va="center", zorder=10):
        ax.text(x, y, s, fontsize=size, fontweight=weight, fontstyle=style,
                 color=color or self.style["ink"], ha=ha, va=va,
                 family="DejaVu Serif", zorder=zorder)

    def _music_glyph(self, ax, x, y, key, size=34, color=None, va="center", zorder=8):
        c = color or self.style["ink"]
        if self.music_prop is not None:
            ax.text(x, y, GLYPH[key], fontsize=size, fontproperties=self.music_prop,
                     color=c, ha="center", va=va, zorder=zorder)
        elif key == "gclef":
            # Text fallback: draw a stylised "G" clef substitute
            ax.text(x, y, "\U0001D11E", fontsize=size, color=c,
                     ha="center", va=va, zorder=zorder,
                     family="serif")

    def _notehead(self, ax, x, y, filled=True, size=None, color=None, stem=True):
        """
        Draw a proper notehead with an optional stem, like a real quarter
        note (filled) or half note (hollow).
        """
        c = color or self.style["ink"]
        # Notehead ellipse — tilted like a real music note
        w = LINE_SPACING * 1.15
        h = LINE_SPACING * 0.80
        face = c if filled else "none"
        lw_head = 1.8 if filled else 1.6
        ax.add_patch(Ellipse((x, y), width=w, height=h, angle=-16,
                               facecolor=face, edgecolor=c, lw=lw_head, zorder=9))
        # Stem — straight vertical line going up from the right of the notehead
        if stem:
            stem_x = x + w * 0.42
            stem_bottom = y
            stem_top = y + STEM_LEN * LINE_SPACING
            ax.plot([stem_x, stem_x], [stem_bottom, stem_top],
                     color=c, lw=1.6, solid_capstyle="round", zorder=9)

    def _x_notehead(self, ax, x, y, size=None, color=None, r=None, lw=2.0):
        c = color or self.style["ink"]
        if r is None:
            r = 0.22 * LINE_SPACING * 2
        ax.plot([x - r, x + r], [y - r, y + r], color=c, lw=lw, zorder=9)
        ax.plot([x - r, x + r], [y + r, y - r], color=c, lw=lw, zorder=9)

    def _target_symbol(self, ax, x, y, r=None, color=None, lw=2.0):
        c = color or self.style["ink"]
        if r is None:
            r = 0.28 * LINE_SPACING * 2
        ax.add_patch(Circle((x, y), r, fill=False, edgecolor=c, lw=lw, zorder=9))
        ax.plot([x - r, x + r], [y, y], color=c, lw=lw, zorder=9)
        ax.plot([x, x], [y - r, y + r], color=c, lw=lw, zorder=9)

    def _control_dot(self, ax, x, y, color=None, r=None):
        c = color or self.style["ink"]
        if r is None:
            r = 0.13 * LINE_SPACING * 2
        ax.add_patch(Circle((x, y), r, fill=True, facecolor=c, edgecolor=c, zorder=9))

    # ---------- staves ----------
    def _draw_staff_lines(self, ax, qubit):
        top = self._staff_top_y(qubit)
        for j in range(N_LINES):
            y = top - j * LINE_SPACING
            ax.plot([BRACE_X, self.end_x], [y, y], color=self.style["ink"],
                     lw=0.8, alpha=0.9, zorder=1)

    def _draw_clef_and_label(self, ax, qubit):
        mid = self._mid_y(qubit)
        # Larger treble clef — should visually fill the staff
        clef_size = max(44, int(80 * LINE_SPACING))
        self._music_glyph(ax, CLEF_X, mid + 0.10 * LINE_SPACING, "gclef",
                           size=clef_size, va="center")
        # Large qubit label styled like a time signature (e.g. "q" over "0")
        self._text(ax, LEFT_LABEL_X, mid + 0.6 * LINE_SPACING,
                    "q", size=20, weight="bold", ha="right", va="center")
        self._text(ax, LEFT_LABEL_X, mid - 0.6 * LINE_SPACING,
                    f"{qubit}", size=20, weight="bold", ha="right", va="center")

    def _draw_initial_state(self, ax, qubit):
        x = X_START - 1.05
        y = self._mid_y(qubit)
        self._notehead(ax, x, y, filled=False, color=self.style["accent"], stem=False)
        self._text(ax, x, y - 1.1 * LINE_SPACING, "|0\u27e9", size=8,
                    style="italic", color=self.style["accent"])

    def _draw_barlines(self, ax, y_top, y_bottom):
        for bx in self._measure_barline_xs():
            ax.plot([bx, bx], [y_top, y_bottom], color=self.style["ink"], lw=1.2, zorder=2)
        # Initial barline after clef/init area
        init_bar_x = (X_START - 1.05 + self.xs[0]) / 2.0 - 0.10 if self.xs else X_START
        ax.plot([init_bar_x, init_bar_x], [y_top, y_bottom],
                 color=self.style["ink"], lw=1.0, zorder=2)
        # Final double/thick barline
        fx = self.end_x - 0.30
        ax.plot([fx - 0.12, fx - 0.12], [y_top, y_bottom],
                 color=self.style["ink"], lw=1.0, zorder=2)
        ax.plot([fx, fx], [y_top, y_bottom],
                 color=self.style["ink"], lw=2.8, zorder=2)

    # ---------- gate rendering ----------
    def _draw_event(self, ax, ev: GateEvent):
        x = self.xs[ev.column]
        ink = self.style["ink"]

        if ev.kind == "barrier":
            y0 = self._y_of(min(ev.qubits), -2.2)
            y1 = self._y_of(max(ev.qubits), 2.2)
            ax.plot([x, x], [y1, y0], color=ink, lw=1.2,
                     ls=(0, (4, 3)), alpha=0.55, zorder=6)
            self._text(ax, x, y1 + 0.6 * LINE_SPACING, "barrier",
                        size=7, style="italic", color=ink)
            return

        if ev.kind == "measure":
            q = ev.targets[0]
            y = self._y_of(q, 0.0)
            self._x_notehead(ax, x, y)
            self._text(ax, x, y - 1.2 * LINE_SPACING, "M",
                        size=9, weight="bold", style="italic")
            return

        if ev.kind == "single":
            q = ev.targets[0]
            off = _pitch_offset(ev)
            y = self._y_of(q, off)
            filled = ev.name != "h"
            self._notehead(ax, x, y, filled=filled, stem=True)
            label_y = y - 1.1 * LINE_SPACING if off >= 0 else y + 1.4 * LINE_SPACING
            self._text(ax, x, label_y, ev.label,
                        size=8, weight="bold", style="italic")
            return

        if ev.kind == "swap":
            q0, q1 = ev.targets[0], ev.targets[1]
            y0, y1 = self._y_of(q0, 0.0), self._y_of(q1, 0.0)
            ax.plot([x, x], [y0, y1], color=ink, lw=1.5, zorder=6)
            r_swap = 0.25 * LINE_SPACING * 2
            self._x_notehead(ax, x, y0, r=r_swap, lw=2.0)
            self._x_notehead(ax, x, y1, r=r_swap, lw=2.0)
            mid_y = (y0 + y1) / 2.0
            self._text(ax, x + 0.6, mid_y, "SWAP",
                        size=8.5, weight="bold", style="italic", ha="left")
            return

        if ev.kind == "control":
            all_q = sorted(ev.qubits)
            y_top = self._y_of(all_q[0], 0.0)
            y_bot = self._y_of(all_q[-1], 0.0)
            ax.plot([x, x], [y_top, y_bot], color=ink, lw=1.5, zorder=6)

            for q in ev.controls:
                self._control_dot(ax, x, self._y_of(q, 0.0))

            for q in ev.targets:
                yt = self._y_of(q, 0.0)
                if ev.name == "cx":
                    self._target_symbol(ax, x, yt)
                elif ev.name == "cz":
                    self._control_dot(ax, x, yt)
                else:
                    self._notehead(ax, x, yt, filled=True, stem=False)

            label_y = (y_top + y_bot) / 2.0
            self._text(ax, x + 0.6, label_y, ev.label,
                        size=8.5, weight="bold", style="italic", ha="left")
            return

        # generic fallback: treat like a "control" block with plain noteheads
        all_q = sorted(ev.qubits)
        y_top = self._y_of(all_q[0], 0.0)
        y_bot = self._y_of(all_q[-1], 0.0)
        if len(all_q) > 1:
            ax.plot([x, x], [y_top, y_bot], color=ink, lw=1.5, zorder=6)
        for q in all_q:
            self._notehead(ax, x, self._y_of(q, 0.0), filled=True, stem=False)
        self._text(ax, x + 0.6, (y_top + y_bot) / 2.0, ev.label,
                    size=8.5, weight="bold", style="italic", ha="left")

    # ---------- public entry point ----------
    def draw(self, figsize=None, dpi=170):
        n = self.n_qubits
        top_y = self._staff_top_y(0) + 1.6
        bottom_y = self._staff_top_y(n - 1) - STAFF_HEIGHT - 1.0
        width = self.end_x + 1.0
        height = top_y - bottom_y

        if figsize is None:
            figsize = (max(10.0, width * 0.72), max(3.0, height * 0.72))

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        fig.patch.set_facecolor(self.style["bg"])
        ax.set_facecolor(self.style["bg"])

        for q in range(n):
            self._draw_staff_lines(ax, q)
            self._draw_clef_and_label(ax, q)
            self._draw_initial_state(ax, q)

        draw_vertical_brace(ax, BRACE_X, top_y - 0.9, bottom_y + 0.9,
                              color=self.style["ink"], lw=2.0)

        self._draw_barlines(ax, top_y - 0.9, bottom_y + 0.9)

        for moment in self.moments:
            for ev in moment:
                self._draw_event(ax, ev)

        if self.title:
            self._text(ax, width / 2.0, top_y + 0.6, self.title, size=15,
                        weight="bold", ha="center", va="bottom")

        ax.set_xlim(-0.3, width)
        ax.set_ylim(bottom_y, top_y + (1.2 if self.title else 0.3))
        ax.set_aspect("equal")
        ax.axis("off")
        fig.tight_layout(pad=0.5)
        return fig


def draw_circuit(qc, filename=None, style="clean", gates_per_measure=3,
                  title=None, dpi=200):
    """
    Renders a qiskit QuantumCircuit as a musical-staff circuit diagram.

    Parameters
    ----------
    qc : qiskit.QuantumCircuit
    filename : str, optional -- if given, saves the figure (png/svg/pdf by extension)
    style : "ink" (aged paper + green ink) or
            "clean" (white background, black ink, good for printing)  ← default
    gates_per_measure : how many circuit "moments" to group between barlines
    title : optional title text drawn above the score

    Returns
    -------
    matplotlib.figure.Figure
    """
    drawer = StaffCircuitDrawer(qc, style=style, gates_per_measure=gates_per_measure, title=title)
    fig = drawer.draw(dpi=dpi)
    if filename:
        fig.savefig(filename, facecolor=fig.get_facecolor(), bbox_inches="tight")
    return fig