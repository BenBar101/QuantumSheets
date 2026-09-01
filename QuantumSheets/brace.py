from matplotlib.path import Path
import matplotlib.patches as patches


def draw_vertical_brace(ax, x, y_top, y_bottom, depth=0.8, color="black", zorder=5):
    """
    Draws a classical curly brace '{' spanning from y_top down to y_bottom,
    with the points extending to the left.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    x : float          – right-edge x position
    y_top, y_bottom    – vertical span
    depth : float      – how far left the tip extends
    color : str        – fill colour
    zorder : int
    """
    y_mid = (y_top + y_bottom) / 2.0
    h = y_top - y_bottom
    w = depth

    # Outer curve (left edge): top → tip → bottom
    # Two cubic Bézier segments (3 CURVE4 codes each)
    verts_outer = [
        (x, y_top),                            # MOVETO  – start
        (x - w * 0.9, y_top - h * 0.01),       # CURVE4  – cp1
        (x - w * 0.2, y_mid + h * 0.1),        # CURVE4  – cp2
        (x - w, y_mid),                         # CURVE4  – tip (endpoint)
        (x - w * 0.2, y_mid - h * 0.1),        # CURVE4  – cp1
        (x - w * 0.9, y_bottom + h * 0.01),    # CURVE4  – cp2
        (x, y_bottom),                          # CURVE4  – bottom (endpoint)
    ]

    # Inner curve (right edge): bottom → tip → top, offset inward by t
    t = 0.25  # thickness at the bulges
    verts_inner = [
        (x - w * 0.9 + t, y_bottom + h * 0.01),  # CURVE4  – cp1
        (x - w * 0.2 + t, y_mid - h * 0.1),      # CURVE4  – cp2
        (x - w + t / 2, y_mid),                    # CURVE4  – inner tip
        (x - w * 0.2 + t, y_mid + h * 0.1),       # CURVE4  – cp1
        (x - w * 0.9 + t, y_top - h * 0.01),      # CURVE4  – cp2
        (x, y_top),                                 # CURVE4  – back to start
    ]

    verts = verts_outer + verts_inner + [(0, 0)]  # dummy vertex for CLOSEPOLY
    codes = [
        Path.MOVETO,
        Path.CURVE4, Path.CURVE4, Path.CURVE4,   # outer: top → tip
        Path.CURVE4, Path.CURVE4, Path.CURVE4,   # outer: tip → bottom
        Path.CURVE4, Path.CURVE4, Path.CURVE4,   # inner: bottom → tip
        Path.CURVE4, Path.CURVE4, Path.CURVE4,   # inner: tip → top
        Path.CLOSEPOLY,
    ]

    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor=color, edgecolor='none', zorder=zorder)
    ax.add_patch(patch)