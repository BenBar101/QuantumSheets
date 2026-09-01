"""
render.py
---------
Draws a qiskit QuantumCircuit as a "musical staff" diagram: one 5-line
staff per qubit, a real treble-clef glyph, actual note shapes for
gates, with proper classical-music typography.

Notes are drawn as vector shapes (matplotlib Ellipse patches) so they
look crisp at any resolution.  Control qubits render as whole notes,
target qubits as filled (black) notes, SWAP as whole-note chords,
and measurements use a long-rest bar with "M" on top.
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
from matplotlib import font_manager

from .layout import circuit_to_moments, GateEvent
from .brace import draw_vertical_brace

_HERE = os.path.dirname(os.path.abspath(__file__))
_CLEF_PATH = os.path.join(_HERE, "clef.png")

# Bravura music font for vector clef glyph (SMuFL U+E050 = treble clef)
_BRAVURA_PATH = os.path.join(_HERE, "Bravura.otf")
try:
    _BRAVURA_PROP = font_manager.FontProperties(fname=_BRAVURA_PATH)
    _BRAVURA_AVAILABLE = os.path.isfile(_BRAVURA_PATH)
except Exception:
    _BRAVURA_AVAILABLE = False

STYLES = {
    "ink":   dict(bg="#efe4c9", ink="#1a1a1a", accent="#c99a2e", paper_edge="#d8c79f"),
    "clean": dict(bg="#ffffff", ink="#1a1a1a", accent="#b8860b", paper_edge="#ffffff"),
}

# ── Geometry ──────────────────────────────────────────────────────────
LINE_SPACING    = 0.55          # tight lines, like real sheet music
N_LINES         = 5
STAFF_HEIGHT    = (N_LINES - 1) * LINE_SPACING
STAFF_GAP       = 1.25          # gap between staves
DX              = 1.6           # horizontal step per moment column
BARRIER_GAP     = 0.4           # extra gap at barrier barlines
X_START         = 5.4           # room for left-bar + clef + time-sig
CLEF_X          = 2.2           # clef close to the left vertical bar
QLABEL_X        = 3.6           # q-label (time signature) after clef
BRACE_X         = 1.25
LEFT_BAR_X      = 1.4           # vertical closing line at far left

# Note geometry – properly proportioned, tilted noteheads
NOTE_W          = 0.55          # width of notehead ellipse (data units)
NOTE_H          = 0.40          # height of notehead ellipse
NOTE_TILT       = 25           # degrees – real noteheads tilt slightly
HALF_LW         = 2.2           # stroke width for half-note ring
WHOLE_W         = 0.56          # whole note width
WHOLE_H         = 0.40
WHOLE_LW        = 2.8           # thicker stroke so whole notes look full
WHOLE_INNER_W   = 0.26          # inner ellipse to create the classic "double-ring" whole note look
WHOLE_INNER_H   = 0.30

STEM_X_OFFSET   = NOTE_W * 0.44  # right edge of notehead
STEM_LW         = 2.5           # stem thickness (thick like real notes)
STEM_LEN        = 3.0 * LINE_SPACING  # stem length
STEM_W          = 0.04          # stem rectangle width (data units)
STEM_Y_PAD      = 0.06          # vertical pad at notehead junction

GATE_LABEL_SIZE = 28            # font size for gate labels (bigger)
QLABEL_SIZE     = 42            # qubit label size – fills the staff top to bottom

# Layout scaling
FIGSIZE_SCALE   = 0.72          # data-units → inches conversion factor
LEDGER_EXTENT   = NOTE_W * 0.7  # half-width of ledger lines

# ── Solfège pitch mapping ─────────────────────────────────────────────
_SOLFEGE = {
    # ── standard gates ──
    "h":      +2.5,     # space above top line
    "x":      +2.0,     # top line
    "sx":     +1.5,     # space below top line
    "sxdg":   +1.5,
    "y":      +1.0,     # 2nd line from top
    "id":      0.0,     # middle line
    "z":      -1.0,     # 2nd line from bottom
    "s":      -2.0,     # bottom line
    "sdg":    -2.0,
    "t":      -3.0,     # ledger line below bottom
    "tdg":    -3.0,
    "reset":  -4.0,     # double ledger line below

    # ── parameterised single-qubit gates ──
    "rx":     +0.5,     # space above middle line
    "ry":     -0.5,     # space below middle line
    "rz":     -1.5,     # space above bottom line
    "p":      -2.5,     # space below bottom line
    
    "u1":     +3.0,     # ledger line above top
    "u2":     +3.5,     # space above ledger line
    "u3":     +4.0,     # double ledger line above
}

def _get_offset_for_name(name: str) -> float:
    if name in _SOLFEGE:
        return _SOLFEGE[name]
    if name.startswith("r"):
        return +1.0
    return 0.0

def _solfege_offset(ev: GateEvent) -> float:
    return _get_offset_for_name(ev.name)

# ── Helper: draw a notehead patch ────────────────────────────────────

def _draw_notehead(ax, x, y, kind="black", ink="#1a1a1a", bg="#ffffff", x_offset=0.0):
    """
    Draw a single notehead centred at (x + x_offset, y).

    kind:
        "black" – filled (quarter-note style)
        "half"  – open ring  (half-note style)
        "whole" – filled ring with inner counter cutout, classic whole-note look
    """
    x_center = x + x_offset
    if kind == "black":
        e = mpatches.Ellipse(
            (x_center, y), NOTE_W, NOTE_H, angle=NOTE_TILT,
            facecolor=ink, edgecolor=ink, linewidth=0.6, zorder=8,
        )
        ax.add_patch(e)
    elif kind == "half":
        e = mpatches.Ellipse(
            (x_center, y), NOTE_W, NOTE_H, angle=NOTE_TILT,
            facecolor="none", edgecolor=ink, linewidth=HALF_LW, zorder=8,
        )
        ax.add_patch(e)
    elif kind == "whole":
        # Outer filled ellipse
        e_out = mpatches.Ellipse(
            (x_center, y), WHOLE_W, WHOLE_H, angle=0,
            facecolor=ink, edgecolor=ink, linewidth=0.6, zorder=8,
        )
        ax.add_patch(e_out)
        # Inner cutout (background colour)
        e_in = mpatches.Ellipse(
            (x_center, y), WHOLE_INNER_W, WHOLE_INNER_H, angle=35,
            facecolor=bg, edgecolor=bg, linewidth=0, zorder=9,
        )
        ax.add_patch(e_in)
    elif kind == "x_note":
        # Draw a thick 'x' cross
        hx = NOTE_W * 0.4
        hy = NOTE_H * 0.5
        ax.plot([x_center - hx, x_center + hx], [y - hy, y + hy], color=ink, lw=3.0, zorder=8)
        ax.plot([x_center - hx, x_center + hx], [y + hy, y - hy], color=ink, lw=3.0, zorder=8)
    else:
        raise ValueError(f"Unknown notehead kind: {kind!r}  (expected 'black', 'half', 'whole', or 'x_note')")



def _draw_stem(ax, stem_x, y_bottom, y_top, ink="#1a1a1a"):
    """Draw a thick stem from y_bottom to y_top on the right edge of the notehead."""
    rect = mpatches.Rectangle(
        (stem_x - STEM_W / 2, y_bottom),
        STEM_W, y_top - y_bottom,
        facecolor=ink, edgecolor='none', zorder=7,
    )
    ax.add_patch(rect)

def _draw_flag(ax, stem_x, stem_top, ink="#1a1a1a"):
    """Draw a classical eighth-note flag curving down from the top of the stem."""
    from matplotlib.path import Path
    
    verts = [
        (0.0, 0.0),            # Start at top-right of stem
        (0.9, 0.2),            # Thick curved top
        (1.5, -1.2),           # Outer swoosh edge
        (0.2, -2.5),           # Sharp inward point
        (1.2, -1.2),           # Inner upward curve
        (0.4, -0.6),           # Thickening inner curve
        (0.0, -1.2),           # Re-attach to stem
        (0.0, 0.0)             # Close path
    ]
    
    codes = [
        Path.MOVETO,
        Path.CURVE4, Path.CURVE4, Path.CURVE4,
        Path.CURVE4, Path.CURVE4, Path.CURVE4,
        Path.CLOSEPOLY
    ]
    
    # Scale factors carefully tuned to fit the stem length
    scaled_verts = [(stem_x + vx * 0.4, stem_top + vy * 0.4) for vx, vy in verts]
    path = Path(scaled_verts, codes)
    patch = mpatches.PathPatch(path, facecolor=ink, edgecolor='none', zorder=8)
    ax.add_patch(patch)

def _draw_measure_symbol(ax, x, y, ink="#1a1a1a"):
    """
    Draw a measurement symbol: a wide, short black rectangle (like the
    classical long-rest / breve-rest bar) with bold 'M' above it.
    """
    bar_w = 0.85   # wide
    bar_h = LINE_SPACING * 0.50  # short – ratio makes it look like a long rest
    rect = mpatches.FancyBboxPatch(
        (x - bar_w / 2, y - bar_h / 2), bar_w, bar_h,
        boxstyle="square,pad=0", facecolor=ink, edgecolor=ink,
        linewidth=0.5, zorder=8,
    )
    ax.add_patch(rect)

    # Bold "M" above the bar
    ax.text(x, y + bar_h / 2 + LINE_SPACING * 0.25, "M",
            fontsize=GATE_LABEL_SIZE + 2, weight="bold", family="DejaVu Serif",
            ha="center", va="bottom", color=ink, zorder=9)


class StaffCircuitDrawer:
    def __init__(self, qc, style="clean", max_cols_per_system=12, title=None, strip=False):
        self.qc = qc
        self.n_qubits = qc.num_qubits
        self.style = STYLES[style]
        self.title = title
        self.moments = circuit_to_moments(qc)
        self.n_cols = len(self.moments)
        self.max_cols_per_system = max(1, self.n_cols) if strip else max(1, max_cols_per_system)
        
        # Split moments into multi-system lines
        self.systems = []
        for i in range(0, self.n_cols, self.max_cols_per_system):
            self.systems.append(self.moments[i:i+self.max_cols_per_system])
            
        if not self.systems:
            self.systems = [[]]

        # Identify barrier columns globally
        self._barrier_cols = set()
        self._empty_barrier_cols = set()
        self._invisible_barrier_cols = set()
        for col_idx, moment in enumerate(self.moments):
            if any(ev.kind == "barrier" for ev in moment):
                self._barrier_cols.add(col_idx)
                if all(ev.kind == "barrier" for ev in moment):
                    self._empty_barrier_cols.add(col_idx)
                    # Make barrier invisible if immediately followed by only measurements
                    if col_idx + 1 < len(self.moments):
                        next_m = self.moments[col_idx + 1]
                        if next_m and all(ev.kind == "measure" for ev in next_m):
                            self._invisible_barrier_cols.add(col_idx)

        self._compute_system_xs()
        self.clef_img = mpimg.imread(_CLEF_PATH)

    # ---------- geometry helpers ----------
    def _compute_system_xs(self):
        self.system_xs = []
        self.system_end_x = []
        
        for sys_idx, sys_moments in enumerate(self.systems):
            xs = []
            x = X_START
            for i, moment in enumerate(sys_moments):
                global_c = sys_idx * self.max_cols_per_system + i
                if i > 0 and global_c in self._barrier_cols:
                    x += BARRIER_GAP
                xs.append(x)
                if global_c not in self._empty_barrier_cols:
                    x += DX
            
            # The final barline is drawn further to the right to clear any beamed chords
            end_x = (xs[-1] if xs else X_START) + DX * 0.6
            self.system_xs.append(xs)
            self.system_end_x.append(end_x)

        # Force all systems to span the expected full page width
        expected_width = X_START + self.max_cols_per_system * DX + 0.6
        actual_max = max(self.system_end_x) if self.system_end_x else expected_width
        page_width = max(expected_width, actual_max)
        self.system_end_x = [page_width] * len(self.systems)

    def _sys_offset_y(self, sys_idx: int) -> float:
        # Each system takes up space for all qubits plus top/bottom padding
        pad_top = 2.4
        pad_bot = 1.6
        height_per_qubit = (STAFF_HEIGHT + STAFF_GAP)
        sys_height = self.n_qubits * height_per_qubit + pad_top + pad_bot
        return -sys_idx * sys_height

    def _staff_top_y(self, qubit: int, sys_idx: int) -> float:
        return self._sys_offset_y(sys_idx) - qubit * (STAFF_HEIGHT + STAFF_GAP)

    def _staff_bottom_y(self, qubit: int, sys_idx: int) -> float:
        return self._staff_top_y(qubit, sys_idx) - STAFF_HEIGHT

    def _mid_y(self, qubit: int, sys_idx: int) -> float:
        return self._staff_top_y(qubit, sys_idx) - (N_LINES // 2) * LINE_SPACING

    def _y_of(self, qubit: int, sys_idx: int, offset: float = 0.0) -> float:
        return self._mid_y(qubit, sys_idx) + offset * LINE_SPACING

    def _global_staff_top(self, sys_idx: int) -> float:
        return self._staff_top_y(0, sys_idx)

    def _global_staff_bottom(self, sys_idx: int) -> float:
        return self._staff_bottom_y(self.n_qubits - 1, sys_idx)

    def _barrier_barline_xs(self, sys_idx: int):
        bl = []
        sys_moments = self.systems[sys_idx]
        xs = self.system_xs[sys_idx]
        for i, moment in enumerate(sys_moments):
            global_c = sys_idx * self.max_cols_per_system + i
            if global_c in self._barrier_cols and global_c not in self._invisible_barrier_cols:
                if i > 0:
                    bl.append((xs[i - 1] + xs[i]) / 2.0)
                else:
                    bl.append(xs[i] - DX * 0.35)
        return bl

    # ---------- drawing primitives ----------
    def _text(self, ax, x, y, text, size=16, weight="normal", style="normal",
              ha="center", va="center", color=None):
        ax.text(x, y, text, fontsize=size, weight=weight, style=style,
                ha=ha, va=va, color=color or self.style["ink"],
                family="DejaVu Serif", zorder=4)

    def _paste_image(self, ax, x, y, img, zoom, zorder=3):
        imagebox = OffsetImage(img, zoom=zoom)
        ab = AnnotationBbox(imagebox, (x, y), frameon=False, pad=0)
        ab.set_zorder(zorder)
        ax.add_artist(ab)

    # ---------- note drawing ----------

    def _notehead(self, ax, x, y, qubit, sys_idx, kind="black", stem=True, flag=False, gate_label=None):
        """
        Draw a notehead with an optional stem and gate label.
        Gate labels are placed to the RIGHT of the notehead.
        Ledger lines are drawn if the note falls outside the 5 staff lines.
        """
        ink = self.style["ink"]

        # 1. Draw ledger lines if necessary
        top_line = self._staff_top_y(qubit, sys_idx)
        bot_line = self._staff_bottom_y(qubit, sys_idx)
        
        # A tiny bit of margin for floating point inaccuracies
        eps = 1e-4
        if y > top_line + eps:
            # Note is above staff
            cur_y = top_line + LINE_SPACING
            while cur_y <= y + eps:
                ax.plot([x - LEDGER_EXTENT, x + LEDGER_EXTENT], [cur_y, cur_y], color=ink, lw=0.8, zorder=1)
                cur_y += LINE_SPACING
        elif y < bot_line - eps:
            cur_y = bot_line - LINE_SPACING
            while cur_y >= y - eps:
                ax.plot([x - LEDGER_EXTENT, x + LEDGER_EXTENT], [cur_y, cur_y], color=ink, lw=0.8, zorder=1)
                cur_y -= LINE_SPACING

        # 2. Draw actual notehead
        def _get_x_offset(k):
            if k == "whole":
                return STEM_X_OFFSET - (WHOLE_W / 2.0)
            elif k == "x_note":
                return STEM_X_OFFSET - (NOTE_W * 0.4)
            return 0.0

        if kind == "measure":
            hx = 0.24
            hy = 0.24
            ax.plot([x - hx, x + hx], [y - hy, y + hy], color=ink, lw=2.8, zorder=8)
            ax.plot([x - hx, x + hx], [y + hy, y - hy], color=ink, lw=2.8, zorder=8)
        else:
            x_off = _get_x_offset(kind)
            _draw_notehead(ax, x, y, kind=kind, ink=ink, bg=self.style["bg"], x_offset=x_off)

        if stem and kind not in ("whole",):
            stem_top = y + STEM_LEN
            stem_x = x + STEM_X_OFFSET
            stem_start = y + NOTE_H * 0.5 if kind == "x_note" else y + STEM_Y_PAD
            _draw_stem(ax, stem_x, stem_start, stem_top, ink=ink)
            if flag:
                _draw_flag(ax, stem_x, stem_top, ink=ink)

        if gate_label:
            # Place label to the right of the note, slightly closer
            label_x = x + NOTE_W * 0.8
            
            # If the label has parameters (parentheses) and is long, put params underneath
            if "(" in gate_label and len(gate_label) > 4:
                base, params = gate_label.split("(", 1)
                params = "(" + params
                
                # Base name next to note
                self._text(ax, label_x, y, base,
                           size=GATE_LABEL_SIZE, weight="bold", style="italic",
                           ha="left", va="center")
                # Params underneath the base name, smaller and normal weight
                self._text(ax, label_x, y - LINE_SPACING * 0.85, params,
                           size=GATE_LABEL_SIZE * 0.75, weight="normal", style="italic",
                           ha="left", va="center")
            else:
                self._text(ax, label_x, y, gate_label,
                           size=GATE_LABEL_SIZE, weight="bold", style="italic",
                           ha="left", va="center")

    def _chord(self, ax, x, qubits, sys_idx, kinds=None, offsets=None, label=None):
        """
        Draw a multi-qubit gate as a musical chord.
        Notes on different staves are connected by a single long stem.
        The gate label sits precisely ON TOP of the stem.
        """
        ink = self.style["ink"]
        if offsets is None:
            offsets = [0.0] * len(qubits)
            
        ys = [self._y_of(q, sys_idx, off) for q, off in zip(qubits, offsets)]
        y_min, y_max = min(ys), max(ys)

        if kinds is None:
            kinds = ["black"] * len(qubits)

        notes = sorted(zip(qubits, ys, kinds), key=lambda item: item[1], reverse=True)
        stem_top = y_max + STEM_LEN
        stem_xs = []

        # Draw all noteheads, their ledger lines, and individual stems
        for i, (q, y_note, kind) in enumerate(notes):
            x_note = x  # all chord notes share the same x-coordinate

            stem_offset = STEM_X_OFFSET
            stem_x = x_note + stem_offset
            stem_xs.append(stem_x)

            top_line = self._staff_top_y(q, sys_idx)
            bot_line = self._staff_bottom_y(q, sys_idx)
            eps = 1e-4
            if y_note > top_line + eps:
                cur_y = top_line + LINE_SPACING
                while cur_y <= y_note + eps:
                    ax.plot([x_note - LEDGER_EXTENT, x_note + LEDGER_EXTENT], [cur_y, cur_y], color=ink, lw=0.8, zorder=1)
                    cur_y += LINE_SPACING
            elif y_note < bot_line - eps:
                cur_y = bot_line - LINE_SPACING
                while cur_y >= y_note - eps:
                    ax.plot([x_note - LEDGER_EXTENT, x_note + LEDGER_EXTENT], [cur_y, cur_y], color=ink, lw=0.8, zorder=1)
                    cur_y -= LINE_SPACING

            def _get_x_offset(k):
                if k == "whole":
                    return STEM_X_OFFSET - (WHOLE_W / 2.0)
                elif k == "x_note":
                    return STEM_X_OFFSET - (NOTE_W * 0.4)
                return 0.0
            
            x_off = _get_x_offset(kind)
            _draw_notehead(ax, x_note, y_note, kind=kind, ink=ink, bg=self.style["bg"], x_offset=x_off)
            
            if kind == "x_note":
                stem_start = y_note + NOTE_H * 0.5
            elif kind == "whole":
                stem_start = y_note
            else:
                stem_start = y_note + STEM_Y_PAD
                
            _draw_stem(ax, stem_x, stem_start, stem_top, ink=ink)

        # Draw horizontal beam connecting all stems at the top
        if len(stem_xs) > 1:
            beam_h = 0.15
            rect = mpatches.Rectangle(
                (min(stem_xs) - STEM_W / 2, stem_top - beam_h),
                max(stem_xs) - min(stem_xs) + STEM_W, beam_h,
                facecolor=ink, edgecolor='none', zorder=7,
            )
            ax.add_patch(rect)

        # Gate label exactly on top of the center of the beam
        if label:
            cx = (min(stem_xs) + max(stem_xs)) / 2.0
            
            if "(" in label:
                base, params = label.split("(", 1)
                params = "(" + params
                
                # Base on the left, closer to beam
                self._text(ax, cx - 0.01, stem_top + LINE_SPACING * 0.02, base,
                           size=GATE_LABEL_SIZE * 1.2, weight="bold", style="italic",
                           ha="right", va="bottom")
                # Params on the right, same height
                self._text(ax, cx + 0.01, stem_top + LINE_SPACING * 0.02, params,
                           size=GATE_LABEL_SIZE * 0.75, weight="normal", style="italic",
                           ha="left", va="bottom")
            else:
                self._text(ax, cx, stem_top + LINE_SPACING * 0.02, label,
                           size=GATE_LABEL_SIZE * 1.2, weight="bold", style="italic",
                           ha="center", va="bottom")

    # ---------- staves ----------
    def _draw_staff_lines(self, ax, qubit, sys_idx):
        top = self._staff_top_y(qubit, sys_idx)
        # Final barline exact position is system_end_x
        fx = self.system_end_x[sys_idx]
        for j in range(N_LINES):
            y = top - j * LINE_SPACING
            # Exact boundary: LEFT_BAR_X to fx (no overshoot)
            ax.plot([LEFT_BAR_X, fx], [y, y], color=self.style["ink"],
                    lw=0.8, alpha=0.9, zorder=1)

    def _draw_clef_and_label(self, ax, qubit, sys_idx):
        ink = self.style["ink"]
        mid = self._mid_y(qubit, sys_idx)

        # Treble clef – vector glyph from Bravura, fallback to raster PNG
        clef_y = mid + LINE_SPACING * 0.5
        if _BRAVURA_AVAILABLE:
            clef_char = '\uE050'  # SMuFL treble clef
            path_clef = TextPath((0, 0), clef_char, size=1, prop=_BRAVURA_PROP)
            bbox_clef = path_clef.get_extents()
            if bbox_clef.width > 0 and bbox_clef.height > 0:
                desired_height = STAFF_HEIGHT * 1.5
                scale_clef = desired_height / bbox_clef.height
                offset_x_clef = CLEF_X - (bbox_clef.x0 + bbox_clef.width / 2.0) * scale_clef
                offset_y_clef = clef_y - (bbox_clef.y0 + bbox_clef.height / 2.0) * scale_clef
                transform_clef = Affine2D().scale(scale_clef).translate(offset_x_clef, offset_y_clef)
                patch_clef = mpatches.PathPatch(
                    path_clef, transform=transform_clef + ax.transData,
                    facecolor=ink, lw=0, zorder=3,
                )
                ax.add_patch(patch_clef)
            else:
                # Glyph missing from font — fall back to raster
                self._paste_image(ax, CLEF_X, clef_y, self.clef_img, zoom=0.065)
        else:
            self._paste_image(ax, CLEF_X, clef_y, self.clef_img, zoom=0.065)

        # Qubit label – fills the WHOLE staff top to bottom like 4/4
        top = self._staff_top_y(qubit, sys_idx)
        bot = self._staff_bottom_y(qubit, sys_idx)
        mid = self._mid_y(qubit, sys_idx)

        # Using serif font to look like time signature, but straight (not italic)
        path_q = TextPath((0, 0), "q", size=1, prop={'family': 'serif', 'weight': 'bold'})
        bbox_q = path_q.get_extents()

        # Scale height exactly to 2 * LINE_SPACING (the top two spaces)
        scale_q = (2.0 * LINE_SPACING) / bbox_q.height
        # Shift down from top line
        offset_y_q = mid - (bbox_q.y0 * scale_q)
        offset_x_q = QLABEL_X - (bbox_q.x0 + bbox_q.width / 2.0) * scale_q

        transform_q = Affine2D().scale(scale_q).translate(offset_x_q, offset_y_q)
        patch_q = mpatches.PathPatch(path_q, transform=transform_q + ax.transData, facecolor=ink, lw=0, zorder=10)
        ax.add_patch(patch_q)

        # Qubit number in the bottom two spaces
        path_n = TextPath((0, 0), str(qubit), size=1, prop={'family': 'serif', 'weight': 'bold'})
        bbox_n = path_n.get_extents()

        scale_n = (2.0 * LINE_SPACING) / bbox_n.height
        offset_y_n = bot - (bbox_n.y0 * scale_n)
        offset_x_n = QLABEL_X - (bbox_n.x0 + bbox_n.width / 2.0) * scale_n

        transform_n = Affine2D().scale(scale_n).translate(offset_x_n, offset_y_n)
        patch_n = mpatches.PathPatch(path_n, transform=transform_n + ax.transData, facecolor=ink, lw=0, zorder=10)
        ax.add_patch(patch_n)

    def _draw_barlines(self, ax, sys_idx):
        """Draw all vertical barlines spanning exactly from the top staff line
        to the bottom staff line — no overshoot."""
        ink = self.style["ink"]
        y_top = self._global_staff_top(sys_idx)
        y_bot = self._global_staff_bottom(sys_idx)

        # Extend exactly enough to cover the staff line thickness (lw=0.8)
        dy = 0.01
        y_top_ext = y_top + dy
        y_bot_ext = y_bot - dy

        # Common vertical bar spanning all staves at the left margin
        ax.plot([LEFT_BAR_X, LEFT_BAR_X], [y_top_ext, y_bot_ext],
                color=ink, lw=1.8, solid_capstyle="butt", zorder=2)

        # Barrier barlines (drawn as solid lines like classical barlines)
        for bx in self._barrier_barline_xs(sys_idx):
            ax.plot([bx, bx], [y_top, y_bot], color=ink, lw=1.4, zorder=2)

        # Closing barline at right end
        fx = self.system_end_x[sys_idx]
        is_final_system = (sys_idx == len(self.systems) - 1)
        
        if is_final_system:
            # Thick double barline only at the very end of the circuit
            ax.plot([fx - 0.3, fx - 0.3], [y_top, y_bot], color=ink, lw=1.2, zorder=2)
            ax.plot([fx, fx], [y_top_ext, y_bot_ext], color=ink, lw=5.0, solid_capstyle="butt", zorder=2)
        else:
            ax.plot([fx, fx], [y_top, y_bot], color=ink, lw=1.0, zorder=2)

    # ---------- gate rendering ----------
    def _draw_event(self, ax, ev: GateEvent, sys_idx: int, local_i: int):
        x = self.system_xs[sys_idx][local_i]
        ink = self.style["ink"]

        if ev.kind == "barrier":
            return

        if ev.kind == "measure":
            q = ev.targets[0]
            y = self._y_of(q, sys_idx, 0.0)
            _draw_measure_symbol(ax, x, y, ink=ink)
            return

        if ev.kind == "single":
            q = ev.targets[0]
            off = _solfege_offset(ev)
            y = self._y_of(q, sys_idx, off)
            kind = "black"
            flag = False
            self._notehead(ax, x, y, q, sys_idx, kind=kind, stem=True, flag=flag, gate_label=ev.label)
            return

        if ev.kind == "swap":
            qubits = sorted([ev.targets[0], ev.targets[1]])
            self._chord(ax, x, qubits, sys_idx, kinds=["x_note", "x_note"], label="SWAP")
            return

        if ev.kind == "control":
            # Derive the base gate name by stripping the control prefix.
            # Use the known control count rather than fragile lstrip('c').
            n_ctrl = len(ev.controls)
            base_name = ev.name[n_ctrl:] if ev.name[n_ctrl:] else ev.name
            target_off = _get_offset_for_name(base_name)

            all_q = sorted(ev.qubits)
            ctrl_set = set(ev.controls)
            kinds = []
            offsets = []
            for q in all_q:
                if q in ctrl_set:
                    # Controls are regular (black) notes
                    kinds.append("black")
                    offsets.append(0.0) 
                else:
                    # Targets are full (whole) notes
                    kinds.append("x_note" if "swap" in ev.name else "whole")
                    offsets.append(target_off)
            self._chord(ax, x, all_q, sys_idx, kinds=kinds, offsets=offsets, label=ev.label)
            return

        # Generic multi-qubit fallback (e.g. rzz, rxx, swap)
        base_name = ev.name
        if ev.name in ("rzz", "rxx", "ryy"):
            base_name = ev.name[-1] # "z", "x", "y"
        target_off = _get_offset_for_name(base_name)
        
        all_q = sorted(ev.qubits)
        offsets = [target_off] * len(all_q)
        target_kind = "x_note" if "swap" in ev.name else "black"
        self._chord(ax, x, all_q, sys_idx, kinds=[target_kind] * len(all_q), offsets=offsets, label=ev.label)

    # ---------- public entry point ----------
    def draw(self, figsize=None, dpi=170):
        n = self.n_qubits
        
        # Calculate full width/height based on systems
        expected_width = X_START + self.max_cols_per_system * DX + 2.0
        actual_max = max(self.system_end_x) + 1.0 if self.system_end_x else expected_width
        max_width = max(expected_width, actual_max)
        y_top_global = self._global_staff_top(0)
        y_bot_global = self._global_staff_bottom(len(self.systems) - 1)
        
        pad_top = 4.5
        pad_bot = 1.5
        height = (y_top_global + pad_top) - (y_bot_global - pad_bot)

        if figsize is None:
            figsize = (max(10.0, max_width * FIGSIZE_SCALE), max(3.0, height * FIGSIZE_SCALE))

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        fig.patch.set_facecolor(self.style["bg"])
        ax.set_facecolor(self.style["bg"])

        # Draw each system
        for sys_idx, sys_moments in enumerate(self.systems):
            y_top = self._global_staff_top(sys_idx)
            y_bot = self._global_staff_bottom(sys_idx)

            for q in range(n):
                self._draw_staff_lines(ax, q, sys_idx)
                self._draw_clef_and_label(ax, q, sys_idx)

            draw_vertical_brace(ax, BRACE_X, y_top, y_bot,
                                color=self.style["ink"])

            self._draw_barlines(ax, sys_idx)

            for i, moment in enumerate(sys_moments):
                for ev in moment:
                    self._draw_event(ax, ev, sys_idx, i)

        if self.title:
            self._text(ax, max_width / 2.0, y_top_global + pad_top - 0.3, self.title, size=15,
                       weight="bold", ha="center", va="bottom")

        ax.set_xlim(-0.3, max_width)
        ax.set_ylim(y_bot_global - pad_bot, y_top_global + pad_top)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.tight_layout(pad=0.5)
        return fig


def draw_circuit(qc, filename=None, style="clean", max_cols_per_system=12,
                 title=None, dpi=200, strip=False):
    drawer = StaffCircuitDrawer(qc, style=style, max_cols_per_system=max_cols_per_system, title=title, strip=strip)
    fig = drawer.draw(dpi=dpi)
    if filename:
        fig.savefig(filename, facecolor=fig.get_facecolor(), bbox_inches="tight")
    return fig